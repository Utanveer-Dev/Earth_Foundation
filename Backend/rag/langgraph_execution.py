from langgraph.graph import StateGraph, END
from .rag_pipeline import StoryCreativityChain
from langchain_core.runnables import RunnablePassthrough
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import Optional, TypedDict
from role_states.adult_states import ADULT_FLOW
from role_states.educator_states import EDUCATOR_FLOW
from role_states.teenager_states import TEENAGER_FLOW
import asyncio
import re, json


# State for LangGraph
class StoryState(TypedDict):
    index: int
    question: str
    needs_retrieval: bool
    answer: Optional[str]
    name: Optional[str]
    email: Optional[str]
    country: Optional[str]
    representation: Optional[str]
    education_setting: Optional[str]
    subjects: Optional[str]
    age_group: Optional[str]
    initiative: Optional[str]
    worked_before: Optional[str]
    date_of_birth: Optional[str]
    in_full_time_secondary_school: Optional[str]
    joining_again: Optional[str]
    formed_team: Optional[str]
    submitted_motivation_statement: Optional[str]
    solution_complete: Optional[str]
    exciting_statement: Optional[str]
    role: Optional[str]
    # interest: Optional[str]
    

# Instantiating chain class once
story_chain = StoryCreativityChain()

main_chain, llm_chain = story_chain.getNewChain()
  
retriever = story_chain.get_retriever_simple()

llm_extract = story_chain.llm

# Node 1: Gating decision + context preparation
def gating_node(state: StoryState):
    
    # print("State Data:", state)
    # print("")
    
    # decision_text = story_chain.create_gating_chain(state["question"])
    
    decision_chain = story_chain.create_gating_chain()
    get_decision = decision_chain.invoke({"input": state["question"]})
    decision_text = get_decision.get('text', '').strip()
    
    memory = ConversationBufferMemory(input_key="question", memory_key="history", max_len=5)
    chat_history = memory.load_memory_variables({}).get("history", [])
    history_text = "\n".join(chat_history) if chat_history else ""

    print("Decision text:", decision_text.startswith("Y"))

    # if state["role"] == "adult":
    #     main_chain, llm_chain = story_chain.getNewChain(ADULT_FLOW)
    # elif state["role"] == "educator":
    #     main_chain, llm_chain = story_chain.getNewChain(EDUCATOR_FLOW)
    # elif state["role"] == "teenager":
        # main_chain, llm_chain = story_chain.getNewChain()

    if decision_text.startswith("Y"):
        # reformulate_chain = story_chain.create_reformulation_chain()
        # get_question = reformulate_chain.invoke({"history": history_text, "input": state["question"]})
        # standalone_question = get_question.get('text', '').strip()

        # docs = story_chain.retriever.get_relevant_documents(standalone_question)
        # context = "\n\n".join([doc.page_content for doc in docs])
        return {"question": state["question"], "needs_retrieval": True}
    else:
        return {"question": state["question"], "context": "", "needs_retrieval": False}


def extract_data_from_index(state: StoryState):
    
    #-------------------------------------------------------- ADULT ROLE EXTRACTION ------------------------------
    if state["role"] == "adult":
    
        if state["index"] == 1 or state["index"] == 3 or state["index"] == 5 or state["index"] == 7:
            
            ADULT_FLOW_LIST = list(ADULT_FLOW.values())
            
            system_instruction, prompt = story_chain.get_flow_step(state["index"], ADULT_FLOW_LIST)
            
            B_INST, E_INST = "[INST]", "[/INST]"
            B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
            
            SYSTEM_PROMPT = B_SYS + system_instruction + '\n' + prompt + E_SYS
            
            instruction = """
            User: {question}"""

            prompt_template = B_INST + SYSTEM_PROMPT + instruction + E_INST
            
            final_prompt = PromptTemplate(input_variables=["question"], template=prompt_template)
            
            llm_chain_extract = LLMChain(prompt=final_prompt, llm=llm_extract)
            
            response = llm_chain_extract.invoke(state["question"])
            
            response_text = response.get("text", "").strip()
        
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))

                    if state["index"] == 1 and "Name" in data:
                        state["name"] = data["Name"]
                        state["index"] += 1

                    elif state["index"] == 3 and "Email" in data:
                        state["email"] = data["Email"]
                        state["index"] += 1

                    elif state["index"] == 5 and "Country" in data:
                        state["country"] = data["Country"]
                        state["index"] += 1

                    elif state["index"] == 7 and "Representation" in data:
                        state["representation"] = data["Representation"]
                        state["index"] += 1

                except json.JSONDecodeError:
                    pass  # If model returns non-JSON, skip

            return state
        
        return state
    
    #-------------------------------------------------------- EDUCATOR ROLE EXTRACTION ------------------------------
    elif state["role"] == "educator":
    
        if state["index"] == 1 or state["index"] == 3 or state["index"] == 5 or state["index"] == 7 or state["index"] == 9 or state["index"] == 11 or state["index"] == 13 or state["index"] == 15:
            
            EDUCATOR_FLOW_LIST = list(EDUCATOR_FLOW.values())
            
            system_instruction, prompt = story_chain.get_flow_step(state["index"], EDUCATOR_FLOW_LIST)
            
            B_INST, E_INST = "[INST]", "[/INST]"
            B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
            
            SYSTEM_PROMPT = B_SYS + system_instruction + '\n' + prompt + E_SYS
            
            instruction = """
            User: {question}"""

            prompt_template = B_INST + SYSTEM_PROMPT + instruction + E_INST
            
            final_prompt = PromptTemplate(input_variables=["question"], template=prompt_template)
            
            llm_chain_extract = LLMChain(prompt=final_prompt, llm=llm_extract)
            
            response = llm_chain_extract.invoke(state["question"])
            
            response_text = response.get("text", "").strip()
        
            print("Extracted Response Text:", response_text)
        
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))

                    if state["index"] == 1 and "Name" in data:
                        state["name"] = data["Name"]
                        state["index"] += 1

                    elif state["index"] == 3 and "Email" in data:
                        state["email"] = data["Email"]
                        state["index"] += 1

                    elif state["index"] == 5 and "Country" in data:
                        state["country"] = data["Country"]
                        state["index"] += 1

                    elif state["index"] == 7 and "Education_setting" in data:
                        state["education_setting"] = data["Education_setting"]
                        state["index"] += 1
                        
                    elif state["index"] == 9 and "Subject(s)" in data:
                        state["subjects"] = data["Subject(s)"]
                        state["index"] += 1
                        
                    elif state["index"] == 11 and "Age_group" in data:
                        state["age_group"] = data["Age_group"]
                        state["index"] += 1
                        
                    elif state["index"] == 13 and "Initiatives" in data:
                        state["initiative"] = data["Initiatives"]
                        state["index"] += 1
                        
                    elif state["index"] == 15 and "Involvment_before" in data:
                        state["worked_before"] = data["Involvment_before"]
                        state["index"] += 1

                except json.JSONDecodeError:
                    pass  # If model returns non-JSON, skip

            return state
        
        return state
    
    #-------------------------------------------------------- TEENAGER ROLE EXTRACTION ------------------------------
    elif state["role"] == "teenager":
    
        if state["index"] == 1 or state["index"] == 3 or state["index"] == 5 or state["index"] == 7 or state["index"] == 9 or state["index"] == 11 or state["index"] == 13 or state["index"] == 14 or state["index"] == 16 or state["index"] == 18 or state["index"] == 20:
            
            TEENAGER_FLOW_LIST = list(TEENAGER_FLOW.values())
            
            system_instruction, prompt = story_chain.get_flow_step(state["index"], TEENAGER_FLOW_LIST)
            
            B_INST, E_INST = "[INST]", "[/INST]"
            B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
            
            SYSTEM_PROMPT = B_SYS + system_instruction + '\n' + prompt + E_SYS
            
            instruction = """
            User: {question}"""

            prompt_template = B_INST + SYSTEM_PROMPT + instruction + E_INST
            
            final_prompt = PromptTemplate(input_variables=["question"], template=prompt_template)
            
            llm_chain_extract = LLMChain(prompt=final_prompt, llm=llm_extract)
            
            response = llm_chain_extract.invoke(state["question"])
            
            response_text = response.get("text", "").strip()
        
            print("Extracted Response Text:", response_text)
        
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))

                    if state["index"] == 1 and "Name" in data:
                        state["name"] = data["Name"]
                        state["index"] += 1

                    elif state["index"] == 3 and "Date_of_birth" in data:
                        state["date_of_birth"] = data["Date_of_birth"]
                        state["index"] += 1

                    elif state["index"] == 5 and "Email" in data:
                        state["email"] = data["Email"]
                        state["index"] += 1

                    elif state["index"] == 7 and "Full_time_secondary_school" in data:
                        state["in_full_time_secondary_school"] = data["Full_time_secondary_school"]
                        state["index"] += 1
                        
                    elif state["index"] == 9 and "Country" in data:
                        state["country"] = data["Country"]
                        state["index"] += 1
                        
                    elif state["index"] == 11 and "Joining_again" in data:
                        state["joining_again"] = data["Joining_again"]
                        state["index"] += 1
                        
                    elif state["index"] == 14 and "Team_formed" in data:
                        state["formed_team"] = data["Team_formed"]
                        state["index"] += 1
                        
                    elif state["index"] == 16 and "Submitted_motivation_statement" in data:
                        state["submitted_motivation_statement"] = data["Submitted_motivation_statement"]
                        state["index"] += 1
                        
                    elif state["index"] == 18 and "Solution_complete" in data:
                        state["solution_complete"] = data["Solution_complete"]
                        state["index"] += 1
                        
                    elif state["index"] == 20 and "Excite_statement" in data:
                        state["exciting_statement"] = data["Excite_statement"]
                        state["index"] += 1

                except json.JSONDecodeError:
                    pass  # If model returns non-JSON, skip

            return state
        
        return state
    
    return state


# Node 2: Run without retrieval
def llm_no_retrieval(state: StoryState):

    print("State Data One:", state)

    state = extract_data_from_index(state)
    
    print("State Data Two:", state)    
    
    if state["role"] == "adult":
        prompt = story_chain.getPromptFromTemplate(state["index"], ADULT_FLOW)
    elif state["role"] == "educator" and state["index"] != 6:
        prompt = story_chain.getPromptFromTemplate(state["index"], EDUCATOR_FLOW)
    elif state["role"] == "teenager" and state["index"] != 10:
        prompt = story_chain.getPromptFromTemplate(state["index"], TEENAGER_FLOW)
    
    
    #------------------------------------------- EDUCATOR ROLE -----------------------------------------------
    if state["role"] == "educator" and state["index"] == 6: 
        # Convert to indexed list
        EDUCATOR_FLOW_LIST = list(EDUCATOR_FLOW.values())

        system_instruction, prompt = story_chain.get_flow_step(state["index"], EDUCATOR_FLOW_LIST)
        
        # system_prompt = "Instruction: " + instruction + "\n" + prompt
        
        B_INST, E_INST = "[INST]", "[/INST]"
        B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
        SYSTEM_PROMPT1 = B_SYS + system_instruction + '\n' + prompt + E_SYS

        instruction = """
        History: {history} \n
        Context: {context} \n
        User: {question}"""

        prompt_template = B_INST + SYSTEM_PROMPT1 + instruction + E_INST
        
        # prompt_template = system_prompt + instruction
        
        prompt = PromptTemplate(input_variables=["country", "history", "question", "context"], template=prompt_template)
    
        llm_chain.prompt = prompt

        temp_retriever = story_chain.get_retriever(state["question"])

        temp_chain = (
            {"country": lambda _: state["country"], "context": temp_retriever, "question": RunnablePassthrough()}
            | llm_chain
        )

        response = temp_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 1
        
    #------------------------------------------- TEENAGER ROLE -----------------------------------------------
    elif state["role"] == "teenager" and state["index"] == 10: 
        # Convert to indexed list
        TEENAGER_FLOW_LIST = list(TEENAGER_FLOW.values())

        system_instruction, prompt = story_chain.get_flow_step(state["index"], TEENAGER_FLOW_LIST)
        
        # system_prompt = "Instruction: " + instruction + "\n" + prompt
        
        B_INST, E_INST = "[INST]", "[/INST]"
        B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
        SYSTEM_PROMPT1 = B_SYS + system_instruction + '\n' + prompt + E_SYS

        instruction = """
        History: {history} \n
        Context: {context} \n
        User: {question}"""

        prompt_template = B_INST + SYSTEM_PROMPT1 + instruction + E_INST
        
        # prompt_template = system_prompt + instruction
        
        prompt = PromptTemplate(input_variables=["country", "history", "question", "context"], template=prompt_template)
    
        llm_chain.prompt = prompt

        temp_retriever = story_chain.get_retriever(state["question"])

        temp_chain = (
            {"country": lambda _: state["country"], "context": temp_retriever, "question": RunnablePassthrough()}
            | llm_chain
        )

        response = temp_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 1
    
       
    #------------------------------------------- EDUCATOR ROLE ----------------------------------------------- 
    elif state["role"] == "educator" and state["index"] == 16 and (state["worked_before"] in ["NO", "No", "no"]): 
    
        llm_chain.prompt = prompt

        temp_chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | llm_chain
        )

        response = temp_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 2
    
    #------------------------------------------- EDUCATOR ROLE -----------------------------------------------
    elif state["role"] == "educator" and state["index"] == 16 and (state["worked_before"] in ["YES", "Yes", "yes"]): 
        
        state["index"] += 1
        
        prompt = story_chain.getPromptFromTemplate(state["index"], EDUCATOR_FLOW)
        
        llm_chain.prompt = prompt

        temp_chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | llm_chain
        )

        response = temp_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 1
        
    #------------------------------------------- TEENAGER ROLE -----------------------------------------------
    elif state["role"] == "teenager" and state["index"] == 12 and (state["joining_again"] in ["YES", "Yes", "yes"]): 
        
        state["index"] += 1
        
        prompt = story_chain.getPromptFromTemplate(state["index"], TEENAGER_FLOW)
        
        llm_chain.prompt = prompt

        temp_chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | llm_chain
        )

        response = temp_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 1
        
    #------------------------------------------- TEENAGER ROLE -----------------------------------------------
    elif state["role"] == "teenager" and state["index"] == 12 and (state["joining_again"] in ["NO", "No", "no"]): 
        
        llm_chain.prompt = prompt

        temp_chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | llm_chain
        )

        response = temp_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 8

    
    else:
        
        print("State Data Three:", state)
        
        llm_chain.prompt = prompt

        temp_chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | llm_chain
        )

        response = temp_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 1  # Increment index for next state

    return state


# Node 3: Run with retrieval
def llm_with_retrieval(state: StoryState):
    
    print("State Data One:", state)
    
    state = extract_data_from_index(state)
        
    print("State Data Two:", state)    
    
    if state["role"] == "adult":
        prompt = story_chain.getPromptFromTemplate(state["index"], ADULT_FLOW)
    elif state["role"] == "educator" and state["index"] != 6:
        prompt = story_chain.getPromptFromTemplate(state["index"], EDUCATOR_FLOW)
    elif state["role"] == "teenager" and state["index"] != 10:
        prompt = story_chain.getPromptFromTemplate(state["index"], TEENAGER_FLOW)
        
        
    #------------------------------------------- EDUCATOR ROLE -----------------------------------------------
    if state["role"] == "educator" and state["index"] == 6: 
        # Convert to indexed list
        EDUCATOR_FLOW_LIST = list(EDUCATOR_FLOW.values())

        system_instruction, prompt = story_chain.get_flow_step(state["index"], EDUCATOR_FLOW_LIST)
        
        # system_prompt = "Instruction: " + instruction + "\n" + prompt
        
        B_INST, E_INST = "[INST]", "[/INST]"
        B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
        SYSTEM_PROMPT1 = B_SYS + system_instruction + '\n' + prompt + E_SYS

        instruction = """
        History: {history} \n
        Context: {context} \n
        User: {question}"""

        prompt_template = B_INST + SYSTEM_PROMPT1 + instruction + E_INST
        
        # prompt_template = system_prompt + instruction
        
        prompt = PromptTemplate(input_variables=["country", "history", "question", "context"], template=prompt_template)
    
        llm_chain.prompt = prompt

        temp_retriever = story_chain.get_retriever(state["question"])

        temp_chain = (
            {"country": lambda _: state["country"], "context": temp_retriever, "question": RunnablePassthrough()}
            | llm_chain
        )

        response = temp_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 1
        
    #------------------------------------------- TEENAGER ROLE -----------------------------------------------
    elif state["role"] == "teenager" and state["index"] == 10: 
        # Convert to indexed list
        TEENAGER_FLOW_LIST = list(TEENAGER_FLOW.values())

        system_instruction, prompt = story_chain.get_flow_step(state["index"], TEENAGER_FLOW_LIST)
        
        # system_prompt = "Instruction: " + instruction + "\n" + prompt
        
        B_INST, E_INST = "[INST]", "[/INST]"
        B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
        SYSTEM_PROMPT1 = B_SYS + system_instruction + '\n' + prompt + E_SYS

        instruction = """
        History: {history} \n
        Context: {context} \n
        User: {question}"""

        prompt_template = B_INST + SYSTEM_PROMPT1 + instruction + E_INST
        
        # prompt_template = system_prompt + instruction
        
        prompt = PromptTemplate(input_variables=["country", "history", "question", "context"], template=prompt_template)
    
        llm_chain.prompt = prompt

        temp_retriever = story_chain.get_retriever(state["question"])

        temp_chain = (
            {"country": lambda _: state["country"], "context": temp_retriever, "question": RunnablePassthrough()}
            | llm_chain
        )

        response = temp_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 1 
        
    #------------------------------------------- EDUCATOR ROLE -----------------------------------------------
    elif state["role"] == "educator" and state["index"] == 16 and (state["worked_before"] in ["NO", "No", "no"]): 
    
        llm_chain.prompt = prompt

        temp_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | llm_chain
        )

        response = temp_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 2
    
    #------------------------------------------- EDUCATOR ROLE -----------------------------------------------
    elif state["role"] == "educator" and state["index"] == 16 and (state["worked_before"] in ["YES", "Yes", "yes"]): 
        
        state["index"] += 1
        
        prompt = story_chain.getPromptFromTemplate(state["index"], EDUCATOR_FLOW)
        
        llm_chain.prompt = prompt

        temp_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | llm_chain
        )

        response = temp_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 1
        
    #------------------------------------------- TEENAGER ROLE -----------------------------------------------
    elif state["role"] == "teenager" and state["index"] == 12 and (state["joining_again"] in ["YES", "Yes", "yes"]): 
        
        state["index"] += 1
        
        prompt = story_chain.getPromptFromTemplate(state["index"], TEENAGER_FLOW)
        
        llm_chain.prompt = prompt

        temp_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | llm_chain
        )

        response = temp_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 1
        
    #------------------------------------------- TEENAGER ROLE -----------------------------------------------    
    elif state["role"] == "teenager" and state["index"] == 12 and (state["joining_again"] in ["NO", "No", "no"]): 
        
        llm_chain.prompt = prompt

        temp_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | llm_chain
        )

        response = temp_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 7    
    
    
    else:
        llm_chain.prompt = prompt
        
        print("State Data Three:", state)
        
        print("")
        print("Education Setting-----------------")
        print("")
        
        main_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | llm_chain
        )

        response = main_chain.invoke(state["question"])
        
        text_response = response.get("text", "").strip()

        # Store plain answer
        state["answer"] = text_response    

        print("")
        print("State:  ", state)
        print("")
        
        state["index"] += 1

    return state


# Building LangGraph
graph = StateGraph(StoryState)

graph.add_node("gating_node", gating_node)
graph.add_node("llm_no_retrieval", llm_no_retrieval)
graph.add_node("llm_with_retrieval", llm_with_retrieval)


# Logic: if needs_retrieval is True → llm_with_retrieval, else → llm_no_retrieval
def route_decision(state: dict):
    return "llm_with_retrieval" if state.get("needs_retrieval") else "llm_no_retrieval"


graph.add_conditional_edges(
    "gating_node",          
    route_decision,        
    {
        "llm_with_retrieval": "llm_with_retrieval",
        "llm_no_retrieval": "llm_no_retrieval"
    }
)

graph.set_entry_point("gating_node")

# Workflow compilation
app = graph.compile()


