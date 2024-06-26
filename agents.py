from dataclasses import dataclass
from crewai_tools import WebsiteSearchTool
from langchain_openai import ChatOpenAI
from crewai_tools.tools import SerperDevTool
from typing import List
from langchain.agents import Tool
from crewai import Agent
from langchain_groq import ChatGroq
from groq import Groq
from langchain_community.utilities import GoogleSerperAPIWrapper
import os

os.getenv("SERPER_API_KEY")


class DreamAnalysisAgents:
    def __init__(self, model:str):
        if model=='chatgpt':
            self.llm = ChatOpenAI(model = "gpt-3.5-turbo")
        else:
            self.llm = ChatGroq(temperature=0, groq_api_key=os.getenv('GROQ_API_KEY'))

        #self.searchInternetTool = SerperDevTool()
        serperInstance = GoogleSerperAPIWrapper()
        search_tool = Tool(
            name="Scrape google searches",
            func=serperInstance.run,
            description="useful for when you need to ask the agent to search the internet",
        )
        self.searchInternetTool = search_tool

    def symbolExtarctorAgent(self, dream:str) -> Agent:
        return Agent(
            role="Jungian Symbols Indentification Expert",
            goal=f"""Generate a List of 3 most relevant jungian symbols present in the following dream.

                Dream: {dream}
                Important:
                - The final list must include only top 3 relevant jungian symbols and nottheir meaning..
                - Do not generate fake information. Only return the information you find. Nothing else!
                - Some Jungian symbols surely exist so try your best.
                - Make sure you the final output does not contain the meaning of symbols but only symbols.
                """,
            backstory="""As an Expert Jungian Analyst, you are responsible for aggregating all the Jungian symbols from the dream
                into a list.""",
            llm=self.llm,
            max_iter = 2,
            verbose=True,
              allow_delegation=False
        )

    def relevantSymbolMeaningAgent(self) -> Agent:
        return Agent(
            role="Jungian Symbols Indentification Expert",
            goal=f"""Write an extensive article using all the scraped data for all symbols from the web
                Important:
                - Make sure that GoogleSerperAPIWrapper.run() takes 2 positional arguments only
                - The article MUST include direct quotations by jung and also book references if any
                - The article should cover most of the scraped data related to the symbols and also references to books mentioned in the scraped data
                - The final text must reference as many symbols as possible scraped from the web.
                - Do not generate fake information. Only return the information you find from the web. Nothing else!
                - Make sure the final output is profound and covers most of the scraped data found from the web extensively.
                - Make sure to break execution and return an empty string in case the serper google api fails
                """,
            backstory="""As a Jungian symbol Agent, you are responsible for aggregating all the researched information
                into an extensive text referencing the scraped data if you werent able to scrape data using the serper tool return an empty string""",
            tools=[self.searchInternetTool],
            llm=self.llm,
            max_iter = 4,
            verbose=True,
             allow_delegation=False
        )
    def summaryAgent(self)->Agent:
        return Agent(
            role="A profound jungian summarizer, expert in giving deep insights from long jungian analysis",
            goal="Summarize the dream analysis received by the relevantSymbolMeaningAgent, provide meaningful and perspective shifting insights in the summary",
            backstory="""You are an Expert Jungian summarizer, a summarizer of a few wise words, your writing is especially reminiscent of jung himself. ONLY use dream analysis received by the previous task for summarizing and nothing else!""",
            verbose=True,
            llm = self.llm,
            max_iter = 2,
              allow_delegation=False
        )

    def finalWriter(self)->Agent:
        return Agent(
            role="The Best Jungian Writer",
            goal="Write a jungian analysis revolving around meanings of symbols returned by the relevantSymbolMeaningAgent",
            backstory="""You are an Expert Jungian analyst, your writing is especially reminiscent of jung himself. You know how to write in
            deep philosophcal and jungian/freudian styles. ONLY use scraped data from the internet extensively""",
            verbose=True,
            llm = self.llm,
            max_iter = 2
        )