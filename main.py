from typing import Any

from dotenv import load_dotenv
from langchain import hub
from langchain_core.tools import Tool
from langchain_experimental.agents import create_csv_agent
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_experimental.tools import PythonREPLTool

load_dotenv()


def main():
    print("Enter main.py")
    instructions = """You are an agent designed to write and execute python code to answer questions.
    You have access to a python REPL, which you can use to execute python code.
    If you get an error, debug your code and try again.
    Only use the output of your code to answer the question. 
    You might know the answer without running any code, but you should still run the code to get the answer.
    If it does not seem like you can write code to answer the question, just return "I don't know" as the answer."""
    base_prompt = hub.pull("langchain-ai/react-agent-template")
    prompt = base_prompt.partial(instructions=instructions)

    tools = [PythonREPLTool()]
    agent = create_react_agent(
        prompt=prompt,
        llm=ChatOpenAI(temperature=0, model="gpt-4"),
        tools=tools
    )

    python_agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    csv_agent = create_csv_agent(
        llm=ChatOpenAI(temperature=0, model="gpt-4"),
        path="episode_info.csv",
        verbose=True,
        allow_dangerous_code=True
    )
    csv_agent_executor = AgentExecutor(agent=csv_agent, tools=tools, verbose=True, handle_parsing_errors=True)

    # Router Grand Agent

    def python_agent_executor_wrapper(original_prompt: str) -> dict[str, Any]:
        return python_agent_executor.invoke({"input": original_prompt})

    tools = [
        Tool(
            name="Python Agent",
            func=python_agent_executor_wrapper.invoke,
            description="""Useful when you need to transform natural language to python and execute the python code,
                        returning the results of the code execution 
                        DOES NOT ACCEPT CODE AS INPUT"""
        ),
        Tool(
            name="CSV Agent",
            func=csv_agent_executor.invoke,
            description="""useful when you need to answer question over episode_info.csv file,
                        takes an input the entire question and returns the answer after running pandas calculation"""
        )
    ]

    prompt = base_prompt.partial(instructions="")
    grand_agent = create_react_agent(
        prompt=prompt,
        llm=ChatOpenAI(temperature=0, model="gpt-4"),
        tools=tools
    )

    grand_agent_executor = AgentExecutor(agent=grand_agent, tools=tools, verbose=True)


if __name__ == '__main__':
    main()
