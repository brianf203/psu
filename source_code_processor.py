from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

class SourceCodeProcessor:
    """
    SourceCodeProcessor is responsible for parsing the source code and extracting API information.
    
    Attributes:
        source_code (str): The source code to be processed.
        llm (LLM): The language model to be used for processing the source code.
    """
    
    def __init__(self, source_code, llm):
        """
        Initializes the SourceCodeProcessor with the given source code and LLM.
        
        Args:
            source_code (str): The source code to be processed.
            llm (LLM): The language model to be used for processing the source code.
        """
        self.source_code = source_code
        self.llm = llm

    def extract_api_information(self):
        """
        Extracts API information from the source code using LLM.
        
        Returns:
            dict: A dictionary containing functions and classes with their signatures and comments.
        """
        api_information = {}
        api_information["functions"] = self._extract_functions(self.source_code)
        api_information["classes"] = self._extract_classes(self.source_code)
        return api_information

    def _extract_functions(self, source_code):
        """
        Extracts function information from the source code using LLM.
        
        Args:
            source_code (str): The source code to extract functions from.
        
        Returns:
            list: A list of dictionaries containing function information.
        """
        prompt_template = PromptTemplate(input_variables=["source_code"], template='Extract the functions from the following source code and return the information in the following JSON format: [{"name": "function_name", "signature": "function_signature", "comments": "function_comments"}, {"name": "function_name2", ...}, ...]\nSource code:\n{source_code}')
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        response = chain.invoke({"source_code": source_code})

        try:
            json_start_index = response.index('[')
            json_end_index = response.rindex(']') + 1
            json_response = response[json_start_index:json_end_index]
            functions = json.loads(json_response)
        except (json.JSONDecodeError, ValueError):
            functions = []

        return functions

    def _extract_classes(self, source_code):
        """
        Extracts class information from the source code using LLM.
        
        Args:
            source_code (str): The source code to extract classes from.
        
        Returns:
            list: A list of dictionaries containing class information.
        """
        prompt_template = PromptTemplate(input_variables=["source_code"], template='Extract the classes from the following source code and return the information in the following JSON format: [{"name": "class_name", "comments": "class_comments", "methods": [{"name": "method_name", "signature": "method_signature", "comments": "method_comments"}, {"name": "method_name2", ...}, ...]}, {"name": "class_name2", ...}, ...]\nSource code:\n{source_code}')
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        response = chain.invoke({"source_code": source_code})

        try:
            json_start_index = response.index('[')
            json_end_index = response.rindex(']') + 1
            json_response = response[json_start_index:json_end_index]
            classes = json.loads(json_response)
        except (json.JSONDecodeError, ValueError):
            classes = []

        return classes

    def generate_query(self):
        """
        Generates a query based on the extracted API information.
        
        Returns:
            str: A query string to find relevant documentation chunks.
        """
        api_info = self.extract_api_information()
        functions = api_info.get("functions", [])
        classes = api_info.get("classes", [])
        
        query = "Functions:\n"
        for func in functions:
            query += f"name: {func['name']}, signature: {func['signature']}, comments: {func['comments"]}\n"
        
        query += "\nClasses:\n"
        for cls in classes:
            query += f"name: {cls['name']}, signature: ({cls['signature']}), comments: ({cls['comments']}), methods: "
            for i, method in enumerate(cls['methods']):
                query += f"({method['name']}, signature: ({method['signature']}), comments: ({method['comments']}))"
                if i < len(cls['methods']) - 1:
                    query += ", "
            query += "\n"
        
        return query
