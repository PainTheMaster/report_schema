from json_io import Array, Objason, Primitive
from typing import Any
from abc import ABC, abstractmethod
import os

#Category
cat_paragraph = 'category_paragraph'
cat_table = 'category_table'

#key
key_cat = 'category'
key_content = 'content'

#Category
descr_key_cat = 'Category of the report component.'


def format_ref(list_ref:list[Any]=None)->str:
    ref = ''
    if list_ref:
        ref_double_quote = [f'"{s}"' for s in list_ref]
        ref = ', '.join(ref_double_quote)
    else:
        ref = 'any relevant documents'
    return ref

def format_scope(list_scope:list[Any]=None)->str:
    ref = ''
    if list_scope:
        ref_double_quote = [f'"{s}"' for s in list_scope]
        ref = ', '.join(ref_double_quote)
    else:
        ref = 'T3-pilot campaign'
    return ref

class Component(ABC):
    @abstractmethod
    def get_schema(self):
        pass

    @abstractmethod
    def get_key(self)->str:
        pass
    
    @abstractmethod
    @staticmethod
    def print_comp(key:str=None, dict_data:dict[str,str]=None)->str:
        pass

class Paragraph(Component):
    def __init__(self, key:str=None, topic:str=None, list_ref:list[Any]=None):
        self.key = key
        self.topic = topic
        ref = format_ref(list_ref=list_ref)
        descrp_paragraph = (f'Please compose a paragrap. The topic of this paragraph is {topic}. Please refer to at least {ref} and any other neccesary material when composing. '
                            f'Please put the result as the property "{key_content}".'
                            'If figures/photos are appropriate, please put a placeholders at the end of the paragraph in the format\n'
                            '   "<placeholder: <description>; <source>; <page>>"\n'
                            'Where:\n'
                            '   -<description>: A short description of the figure/photo.\n'
                            '   -<source>: The source file.\n'
                            '   -<page>: Page number in the source file.\n'
                            'Please compose in Japanese language. The paragraph can be as long as needed.')
        content = Primitive(prim_type='string',
                            key=key_content,
                            description=f'This property is to contain sentences composing the paragraph.')
        cat = Primitive(prim_type='string',
                        key=key_cat,
                        description=descr_key_cat,
                        const=cat_paragraph)
        self.obj_paragraph = Objason(key=key,
                                     props=[cat, content],
                                     description=descrp_paragraph)

    def get_schema(self)-> Objason:
        return self.obj_paragraph

    def get_key(self):
        return self.key

    @staticmethod
    def print_comp(key = None, dict_data:dict[str, str]=None)->str:
        content_str = dict_data.get(key_content, f'!!!ERROR: No content given for the paragraph "{key}"')
        return content_str



class Table(Component):
    def __init__(self, key:str=None, topic:str=None, list_scope:list[Any]=None, list_ref:list[Any]=None):
        self.key = key
        self.topic = topic
        ref = format_ref(list_ref=list_ref)
        scope = format_scope(list_scope=list_scope)
        
        descrp_table = f'Please place a table in the CSV format with a header. The topic of the table is {topic}, and the scope of the table, in terms of production campaign, is {scope}. For data, please refer to {ref} '
        content = Primitive(prim_type='string',
                            key=key_content,
                            description='This property is to contain a table in the CSV format with a header.')
        cat = Primitive(prim_type='string',
                        key=key_cat,
                        description=descr_key_cat,
                        const=cat_table)
        self.obj_table = Objason(key=key,
                                 props=[cat, content],
                                 description=descrp_table)

    def get_schema(self)->Objason:
        return self.obj_table

    def get_key(self):
        return self.key

    @staticmethod
    def print_comp(key=None, dict_data:dict[str, str]=None)->str:
        csv = dict_data.get(key_content)
        file_name_stem = f'table_{key}'
        n = 1
        file_name = file_name_stem+'.csv'
        if not os.path.isfile(file_name):
            with open(file=file_name, mode='x') as f:
                f.write(csv)
        else:
            while os.path.isfile(f'{file_name_stem}_{n}.csv'):
                n += 1
            file_name = f'{file_name_stem}_{n}.csv'
            with open(file=file_name, mode='x') as f:
                f.write(csv)
        
        return f'\nRefer to "{file_name}" for the table.\n'
        
        
class Section(Component):
    def __init__(self, key:str=None, title:str=None, topic:str=None, list_comp:list[Component]=None):
        self.key=key
        self.title = title
        self.topic = topic
        self.list_comp = list_comp

        descrp = ''
        if topic:
            descrp=f'One section in the report. the title is "{title}" dealing with {topic}.'
        else:
            descrp=f'One section in the report. the title is "{title}".'
        schema_comp = [c.get_schema() for c in list_comp]
        self.schema = Objason(key=key,
                              props=schema_comp,
                              description=descrp)

    def get_schema(self)->Objason:
        return self.schema

    def get_key(self):
        return self.key


    @staticmethod
    def print_comp(key=None, dict_data:dict[str, str] = None):
        pass

    def compose(self, dict_data:dict[str, dict]=None) -> str:
        str_section = self.title+'\n'
        for comp in self.list_comp:
            key_this = comp.get_key()
            dict_comp = dict_data[key_this]
            if isinstance(comp, Paragraph):
                str_section += Paragraph.print_comp(key=key_this, dict_data=dict_comp)
                str_section += '\n'
            if isinstance(comp, Table):
                str_section += Table.print_comp(key=key_this, dict_data=dict_comp)

class Chapter(Component):
    def __init__(self, key:str=None, title:str=None, ):
        

        


