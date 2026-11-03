from json_io import Array, Objason, Primitive
from typing import Any
from abc import ABC, abstractmethod
import csv
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
key_header_table = 'header'
key_rows_table = 'rows'

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

def check_children(owner:str, list_child:list['Component'], name_list:str):
    '''Raises ValueError if the list of child components is empty or has duplicated keys.'''
    if not list_child:
        raise ValueError(f'{owner}: "{name_list}" is empty.')
    list_key = [c.get_key() for c in list_child]
    list_dup = sorted({k for k in list_key if list_key.count(k) > 1})
    if list_dup:
        raise ValueError(f'{owner}: Duplicated keys in "{name_list}": {list_dup}')

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
    def __init__(self, key:str=None, topic:str=None,  user_message:str=None, list_scope:list[Any]=None, list_ref:list[Any]=None,
                 columns:list[str|Primitive]=None):
        '''
        columns: Column definitions of the table. Each entry is either a column name (str) or a Primitive whose key is the column name.
                 If given, each row is received as an object keyed by the column names.
                 If not given, the header is decided by the LLM and each row is received as an array.
        '''
        self.key = key
        self.topic = topic
        self.columns:list[Primitive]|None = None
        if columns:
            self.columns = [Primitive(prim_type=['string', 'number'], key=c, nullable=True) if isinstance(c, str) else c
                            for c in columns]
            list_col_key = [c.key for c in self.columns]
            if len(set(list_col_key)) != len(list_col_key):
                raise ValueError(f'{self.__class__.__name__}("{key}"): Duplicated column names in "columns".')
        # ref = format_ref(list_ref=list_ref)
        # scope = format_scope(list_scope=list_scope)
        ref = format_list(list_ref, default='any relevant documents')
        scope = format_list(list_scope, default='T3-pilot campaign')

        if not user_message:
            user_message = ''
        else:
            user_message = "\nAdditional message: "+user_message
        
        descrp_table = (f'Please place a table. The topic of the table is {topic}, and the scope of the table, in terms of production campaign, is {scope}. '
                        f'For data, please refer to {ref}. '
                        'Put one cell value per element. Use null for an empty cell.'+user_message)
        if self.columns:
            row = Objason(key='row',
                          props=self.columns,
                          description='One row of the table. Each property corresponds to the column of the same name.')
            content = Array(key=key_content,
                            content=row,
                            description='Rows of the table, from top to bottom. The header is not included.')
        else:
            header = Array(key=key_header_table,
                           content=Primitive(prim_type='string', key='column_name'),
                           description='Column names of the table, from left to right.')
            cell = Primitive(prim_type=['string', 'number'], key='cell', nullable=True)
            rows = Array(key=key_rows_table,
                         content=Array(key='row', content=cell, description='One row of the table. Cells are in the same order as "header".'),
                         description='Rows of the table, from top to bottom. Every row must have the same number of cells as "header".')
            content = Objason(key=key_content,
                              props=[header, rows],
                              description='This property is to contain a table.')
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
        table = self.__to_rows(dict_this.get(key_content))
        if table is None:
            return f'!!!ERROR: Invalid table data for the table "{self.key}"\n'
        file_name_stem = f'table_{self.key}'

        file_name = f'{file_name_stem}.csv'
        n = 1
        while os.path.isfile(file_name):
            file_name = f'{file_name_stem}_{n}.csv'
            n += 1
        # newline='' is required by csv.writer, which puts "\r\n" at the end of each line by itself.
        with open(file=file_name, mode='x', encoding='utf-8-sig', newline='') as f:
            csv.writer(f).writerows(table)

        footnote = dict_this.get(key_footnote_table)
        if footnote:
            return (f'\nRefer to "{file_name}" for the table.\n'
                    f'<footnote>: {footnote}\n\n')
        else:
            return f'\nRefer to "{file_name}" for the table.\n\n'

    def __to_rows(self, content:Any)->list[list[Any]]|None:
        '''Converts the "content" received from the LLM to a list of rows including the header. Returns None if the shape is invalid.'''
        def cell(value:Any)->Any:
            return '' if value is None else value

        if self.columns:
            if not isinstance(content, list):
                return None
            list_col_key = [c.key for c in self.columns]
            table = [list_col_key]
            for row in content:
                if not isinstance(row, dict):
                    return None
                table.append([cell(row.get(k)) for k in list_col_key])
            return table

        if not isinstance(content, dict):
            return None
        header = content.get(key_header_table)
        rows = content.get(key_rows_table)
        if not isinstance(header, list) or not isinstance(rows, list):
            return None
        table = [header]
        for row in rows:
            if not isinstance(row, list):
                return None
            # Pads short rows so that every line of the CSV has the same number of columns as the header.
            row = [cell(v) for v in row]
            row += [''] * (len(header) - len(row))
            table.append(row)
        return table


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

        if topic:
            self.descrp=(f'One section in the report. the title is "{title}" dealing with {topic}. '
                         'A section can have multiple paragraphs, tables, and figures. For details, please follow the instructions of each component.')
        else:
            self.descrp=(f'One section in the report. the title is "{title}". '
                         'A section can have multiple paragraphs, tables, and figures. For details, please follow the instructions of each component.')

    def get_schema(self)->Objason:
        # The schema is built here, not in __init__(), so that components added by add_component() are included.
        check_children(owner=f'{self.__class__.__name__}("{self.key}")', list_child=self.list_comp, name_list='list_comp')
        schema_comp = [c.get_schema() for c in self.list_comp]
        content = Objason(key=key_content,
                          props=schema_comp,
                          description='The main content of a section.')
        cat = Primitive(prim_type='string',
                        key=key_cat,
                        description=descr_key_cat,
                        const=cat_sect)
        return Objason(key=self.key,
                       props=[cat, content],
                       description=self.descrp)

    def get_key(self):
        return self.key

    def add_component(self, comp:Component):
        self.list_comp.append(comp)

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

        if topic:
            self.descrp=(f'One chapter in the report. the title is "{title}" dealing with {topic}. A chapter can contain multiple sections as its contents. '
                         'For contents, please, follow the instructions of each section, paragraph, and table. ')
        else:
            self.descrp=(f'One chapter in the report. the title is "{title}". '
                         'For contents, please, follow the instructions of each section, paragraph, and table. ')

    def add_section(self, sect:Section):
        self.list_sect.append(sect)

    def get_schema(self)->Objason:
        # The schema is built here, not in __init__(), so that sections added by add_section() are included.
        check_children(owner=f'{self.__class__.__name__}("{self.key}")', list_child=self.list_sect, name_list='list_sect')
        schema_sect = [s.get_schema() for s in self.list_sect]
        content = Objason(key = key_content,
                          props=schema_sect,
                          description='The main content of the chapter.')
        cat = Primitive(prim_type='string',
                        key=key_cat,
                        description=descr_key_cat,
                        const=cat_chapt)
        return Objason(key=self.key,
                       props=[cat, content],
                       description=self.descrp)

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


class Report:
    def __init__(self, list_chapt:list[Chapter]=None, description:str=None):
        if list_chapt is None:
            list_chapt = []
        self.list_chapt = list_chapt
        if not description:
            description = ('A report consisting of chapters. '
                           'For contents, please follow the instructions of each chapter, section, paragraph, and table.')
        self.description = description

    def add_chapter(self, chapt:Chapter):
        self.list_chapt.append(chapt)

    def get_schema(self)->dict[str, Any]:
        '''Returns the JSON Schema of the whole report. The top level of the JSON data is {<chapter key>: <chapter>, ...}, which is what compose() receives.'''
        check_children(owner=self.__class__.__name__, list_child=self.list_chapt, name_list='list_chapt')
        schema = Objason(key='report',
                         props=[c.get_schema() for c in self.list_chapt],
                         description=self.description)
        _, dict_schema = schema.as_dict()
        return {'$schema': 'https://json-schema.org/draft/2020-12/schema', **dict_schema}

    def compose(self, dict_data = None)->str:
        str_output = ''
        for chapt in self.list_chapt:
            str_output += chapt.compose(dict_data)

        with open(file='report.txt', mode='w', encoding='utf-8') as f:
            f.write(str_output)
        
        return str_output

    
        

        


