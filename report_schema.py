from json_io import Array, Objason, Primitive
from typing import Any
from abc import ABC, abstractmethod
import os

#Category
cat_paragraph = 'category_paragraph'
cat_table = 'category_table'
cat_sect = 'category_section'
cat_chapt = 'category_chapter'

#key
key_cat = 'category'
key_content = 'content'
key_footnote_table = 'footnote_for_table'

#Category
descr_key_cat = 'Category of the report component.'


# def format_ref(list_ref:list[Any]=None)->str:
#     ref = ''
#     if list_ref:
#         ref_double_quote = [f'"{s}"' for s in list_ref]
#         ref = ', '.join(ref_double_quote)
#     else:
#         ref = 'any relevant documents'
#     return ref

# def format_scope(list_scope:list[Any]=None)->str:
#     ref = ''
#     if list_scope:
#         ref_double_quote = [f'"{s}"' for s in list_scope]
#         ref = ', '.join(ref_double_quote)
#     else:
#         ref = 'T3-pilot campaign'
#     return ref

def format_list(list_itms:list[Any]=None, default:str='<placeholder>')->str:
    if not list_itms:
        return default
    return ', '.join([f'"{i}"' for i in list_itms])

class Component(ABC):
    @abstractmethod
    def get_schema(self):
        pass

    @abstractmethod
    def get_key(self)->str:
        pass
    
    @abstractmethod
    def compose(self, dict_data:dict[str,dict]=None)->str:
        pass

class Paragraph(Component):
    def __init__(self, key:str=None, topic:str=None, user_message:str=None, list_ref:list[Any]=None):
        self.key = key
        self.topic = topic
        # ref = format_ref(list_ref=list_ref)
        ref = format_list(list_ref, default='any relevant documents')

        if not user_message:
            user_message = ''
        else:
            user_message = "\nAdditional message: "+user_message

        descrp_paragraph = (f'Please compose a paragraph. The topic of this paragraph is {topic}. Please refer to at least {ref} and any other necessary material when composing. '
                            f'Please put the result as the property "{key_content}". '
                            'If figures/photos are appropriate, please put placeholders at the end of the paragraph in the format\n'
                            '   "<placeholder: <description>; <source>; <page>>"\n'
                            'Where:\n'
                            '   -<description>: A short description of the figure/photo.\n'
                            '   -<source>: The source file.\n'
                            '   -<page>: Page number in the source file.\n'
                            'Please compose in Japanese language. The paragraph can be as long as needed.'+user_message)
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

    def compose(self, dict_data:dict[str, str]=None)->str:
        dict_this = dict_data.get(self.key)
        content_str = ''
        if dict_this:
            content_str = dict_this.get(key_content,'')+'\n'
        else:
            content_str = f'!!!ERROR: No content given for the paragraph "{self.key}"\n'
        return content_str

class Table(Component):
    def __init__(self, key:str=None, topic:str=None,  user_message:str=None, list_scope:list[Any]=None, list_ref:list[Any]=None):
        self.key = key
        self.topic = topic
        # ref = format_ref(list_ref=list_ref)
        # scope = format_scope(list_scope=list_scope)
        ref = format_list(list_ref, default='any relevant documents')
        scope = format_list(list_scope, default='T3-pilot campaign')

        if not user_message:
            user_message = ''
        else:
            user_message = "\nAdditional message: "+user_message
        
        descrp_table = (f'Please place a table in the CSV format with a header. The topic of the table is {topic}, and the scope of the table, in terms of production campaign, is {scope}. '
                        f'For data, please refer to {ref}.'+user_message)
        content = Primitive(prim_type='string',
                            key=key_content,
                            description='This property is to contain a table in the CSV format with a header.')
        footnote = Primitive(prim_type='string',
                             key=key_footnote_table,
                             description=('This property is to contain footnotes for the table. Can contain multiple notes. '
                                          'Please enumerate the notes and the corresponding contents in the table to link them properly. '
                                          'Please compose in Japanese language.'),
                             nullable=True,
                             required=False) 
        cat = Primitive(prim_type='string',
                        key=key_cat,
                        description=descr_key_cat,
                        const=cat_table)
        self.obj_table = Objason(key=key,
                                 props=[cat, content, footnote],
                                 description=descrp_table)

    def get_schema(self)->Objason:
        return self.obj_table

    def get_key(self):
        return self.key

    def compose(self, dict_data:dict[str, str]=None)->str:
        dict_this = dict_data.get(self.key)
        if not dict_this:
            return f'For key "{self.key}", table data is empty.\n'
        csv = dict_this.get(key_content, '"<empty_table>"')
        file_name_stem = f'table_{self.key}'

        file_name = f'{file_name_stem}.csv'
        n = 1
        while os.path.isfile(file_name):
            file_name = f'{file_name_stem}_{n}.csv'
            n += 1
        with open(file=file_name, mode='x', encoding='utf-8-sig', newline='') as f:
            f.write(csv)

        footnote = dict_this.get(key_footnote_table)
        if footnote:
            return (f'\nRefer to "{file_name}" for the table.\n'
                    f'<footnote>: {footnote}\n\n')
        else:
            return f'\nRefer to "{file_name}" for the table.\n\n'
        
        
class Section(Component):
    def __init__(self, key:str=None, title:str=None, topic:str=None, list_comp:list[Component]=None):
        self.key=key
        if not title:
            title = '<no title>'
        self.title = title
        self.topic = topic
        if list_comp is None:
            list_comp = []
        self.list_comp = list_comp

        descrp = ''
        if topic:
            descrp=(f'One section in the report. the title is "{title}" dealing with {topic}. '
                    'A section can have multiple paragraphs, tables, and figures. For details, please follow the instructions of each component.')
        else:
            descrp=(f'One section in the report. the title is "{title}". '
                    'A section can have multiple paragraphs, tables, and figures. For details, please follow the instructions of each component.')

        schema_comp = [c.get_schema() for c in list_comp]
        content = Objason(key=key_content,
                          props=schema_comp,
                          description='The main content of a section.')
        cat = Primitive(prim_type='string',
                        key=key_cat,
                        description=descr_key_cat,
                        const=cat_sect)
        self.schema = Objason(key=key,
                              props=[cat, content],
                              description=descrp)
        
    def get_schema(self)->Objason:
        return self.schema

    def get_key(self):
        return self.key

    def compose(self, dict_data:dict[str, dict]=None) -> str:
        str_section = '\n\n'+self.title+'\n'
        dict_this = dict_data.get(self.key)
        if not dict_this:
            return f'For a section key "{self.key}", the JSON has no data.\n'
        dict_contents = dict_this.get(key_content) or {}
        for comp in self.list_comp:
            str_section += comp.compose(dict_data=dict_contents)
        return str_section


class Chapter(Component):
    def __init__(self, key:str=None, title:str=None, topic:str=None, list_sect:list[Section]=None):
        self.key = key
        if not title:
            title = '<no title>'
        self.title = title
        self.topic = topic
        if list_sect is None:
            list_sect = []
        self.list_sect = list_sect

        descrp = ''
        if topic:
            descrp=(f'One chapter in the report. the title is "{title}" dealing with {topic}. A chapter can contain multiple sections as its contents. '
                    'For contents, please, follow the instructions of each section, paragraph, and table. ')
        else:
            descrp=(f'One chapter in the report. the title is "{title}". '
                    'For contents, please, follow the instructions of each section, paragraph, and table. ')

        schema_sect = [s.get_schema() for s in list_sect]
        content = Objason(key = key_content,
                          props=schema_sect,
                          description='The main content of the chapter.')
        cat = Primitive(prim_type='string',
                        key=key_cat,
                        description=descr_key_cat,
                        const=cat_chapt)
        self.schema = Objason(key=key,
                              props=[cat, content],
                              description=descrp)

    def get_schema(self):
        return self.schema

    def get_key(self):
        return self.key

    def compose(self, dict_data = None):
        dict_this = dict_data.get(self.key)
        if not dict_this:
            return f'For key "{self.key}", the input JSON has no data.\n'
        str_output = f'\n\n{self.title}\n'
        dict_contents = dict_this.get(key_content) or {}
        for sect in self.list_sect:
            str_output += sect.compose(dict_contents)
        return str_output

    
        
        

        


