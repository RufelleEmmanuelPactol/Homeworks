from pyexpat.errors import messages
from typing import Any
from openai import OpenAI
import dotenv
dotenv.load_dotenv()

class Template:
    """
        For templates, we need to define
    """

    def __init__(self, kwargs=None, prepended_history=None, ):
        if kwargs is None:
            kwargs = {}
        if prepended_history is None:
            prepended_history = []
        self.history = prepended_history
        self.kwargs = kwargs

    def system(self, query, kwargs=None):
        if kwargs is None:
            kwargs = {}
        self.history.append({"role": "system", "content": query.format(**kwargs)})
        return self

    def user(self, query, kwargs=None):
        if kwargs is None:
            kwargs = {}
        self.history.append({"role": "user", "content": query.format(**kwargs)})
        return self



class Call:


    def __init__(self, template: Template):
        self.template = template
        self.history = template.history.copy()
        self.llm = OpenAI()




    def converse(self, query, args=None):
        if args is None:
            args = {}
        query = query.format(**args)
        self.history.append({"role": "user", "content": query})
        return self.llm.chat.completions.create(
            model='gpt-4o',
            messages=self.history
        ).choices[0].message.content














