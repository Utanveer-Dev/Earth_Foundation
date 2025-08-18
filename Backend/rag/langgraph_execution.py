from langgraph.graph import StateGraph, END
from .rag_pipeline import StoryCreativityChain
from langchain_core.runnables import RunnablePassthrough
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import Optional, TypedDict
from role_states.adult_states import ADULT_FLOW
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
    role: Optional[str]
    # interest: Optional[str]
    

# Instantiating chain class once
story_chain = StoryCreativityChain()
main_chain, llm_chain = story_chain.getNewChain()

retriever = story_chain.get_retriever()

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

    if decision_text.startswith("Y"):
        # reformulate_chain = story_chain.create_reformulation_chain()
        # get_question = reformulate_chain.invoke({"history": history_text, "input": state["question"]})
        # standalone_question = get_question.get('text', '').strip()

        # docs = story_chain.retriever.get_relevant_documents(standalone_question)
        # context = "\n\n".join([doc.page_content for doc in docs])
        return {"question": state["question"], "needs_retrieval": True}
    else:
        return {"question": state["question"], "context": "", "needs_retrieval": False}


def extract_data_from_index(state: StoryState, response_text: str):
    
    match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))

            if state["index"] == 1 and "Name" in data:
                state["name"] = data["Name"]

            elif state["index"] == 3 and "Email" in data:
                state["email"] = data["Email"]

            elif state["index"] == 5 and "Country" in data:
                state["country"] = data["Country"]

            elif state["index"] == 7 and "Representation" in data:
                state["representation"] = data["Representation"]

            # elif state["index"] == 9 and "Interest" in data:
            #     state["interest"] = data["Interest"]

        except json.JSONDecodeError:
            pass  # If model returns non-JSON, skip

    return state



# Node 2: Run without retrieval
def llm_no_retrieval(state: StoryState):
   
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
        
        text_response = response.get("text", "").strip()

        state = extract_data_from_index(state, text_response)

        state["index"] += 1
        
    prompt = story_chain.getPromptFromTemplate(state["index"])
    
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
        
        text_response = response.get("text", "").strip()

        state = extract_data_from_index(state, text_response)

        state["index"] += 1
        
    prompt = story_chain.getPromptFromTemplate(state["index"])
    
    llm_chain.prompt = prompt
    
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


