from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import asyncio
from rag.langgraph_execution import app
from .models import Customer
from .serializers import CustomerSerializer
import os


class StoryCreativityAPIView(APIView):
    # In-memory tracker (optional, still useful for session-like behavior)
    user_indices = {}

    def post(self, request):
        user_id = 11  
        q = request.data.get("question", "").strip()
        if not q:
            return Response({"error": "No question provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Get current index for this user, default 0
        index = self.user_indices.get(user_id, 0)

        # "education_setting", "subjects", "age_group", "initiative", "worked_before"

        # Fetch existing customer from DB (if exists)
        customer = Customer.objects.filter(id=user_id).first()  # replace with dynamic lookup if needed
        serializer = None
        if customer:
            serializer = CustomerSerializer(customer)
            name = customer.name
            email = customer.email
            country = customer.country
            representation = customer.representation
            education_setting = customer.education_setting
            subjects = customer.subjects
            age_group = customer.age_group
            initiative = customer.initiative
            worked_before = customer.worked_before
            state = customer.state
            role = customer.role
        else:
            name = email = country = representation = state = role = education_setting = subjects = age_group = initiative = worked_before = None

        role = request.data.get("role", "").strip().lower()

        if role == "adult":

            # Build state for LangGraph 
            state = {
                "index": index,
                "question": q, 
                "needs_retrieval": False,
                "answer": None,
                "name": name,
                "email": email,
                "country": country,
                "representation": representation,
                "role": role
            }
            
        elif role == "educator":

            # Build state for LangGraph 
            state = {
                "index": index,
                "question": q, 
                "needs_retrieval": False,
                "answer": None,
                "name": name,
                "email": email,
                "country": country,
                "education_setting": education_setting,
                "subjects": subjects,
                "age_group": age_group,
                "initiative": initiative,
                "worked_before": worked_before,
                "role": role
            }

        try:
            # Run LangGraph
            updated_state = asyncio.run(app.ainvoke(state, config={"configurable": {"session_id": user_id}}))

            # Update index tracker
            self.user_indices[user_id] = updated_state.get("index", index)

            # --- Sync DB (Create or Update customer) ---
            customer_data = {
                "name": updated_state.get("name", name),
                "email": updated_state.get("email", email),
                "country": updated_state.get("country", country),
                "representation": updated_state.get("representation", representation),
                "education_setting": updated_state.get("education_setting", education_setting),
                "subjects": updated_state.get("subjects", subjects),
                "age_group": updated_state.get("age_group", age_group),
                "initiative": updated_state.get("initiative", initiative),
                "worked_before": updated_state.get("worked_before", worked_before),
                "state": updated_state.get("index", index)-1,
                "role": updated_state.get("role", role),
            }

            if customer:
                # Update existing
                serializer = CustomerSerializer(customer, data=customer_data, partial=True)
            else:
                # Create new
                serializer = CustomerSerializer(data=customer_data, partial=True)

            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "answer": updated_state.get("answer"),
                "customer": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)