from abc import ABC, abstractmethod
from typing import Literal, Any
import json

class JsonEntity(ABC):
    def __init__(self,
                 key:str=None,
                 description:str=None,
                 required:bool=True):
        self.key=key
        self.description=description
        self.required=required

    @abstractmethod
    def asType(self)->list[str]:
        pass

    @abstractmethod
    def asEntity(self)->list[str]:
        pass

    @abstractmethod
    def as_dict(self)->tuple[str, dict[str,Any]]:
        pass

    def json_literal(self, value: str|int|float|bool) -> str:
        return json.dumps(value, ensure_ascii=False)

class Array(JsonEntity):
    def __init__(self,
                key:str=None,
                content:JsonEntity | list[JsonEntity]=None,
                description:str=None,
                required:bool=True,
                nullable:bool=None):
        super().__init__(key=key, description=description, required=required)
        self.content=content
        self.nullable = nullable
        if key is None:
            raise ValueError(f'{self.__class__.__name__}: "key" not given.')        
        if content is None:
            raise ValueError(f'{self.__class__.__name__}: "content" not given.')
        if isinstance(self.content, list) and len(self.content) == 0:
            raise ValueError(f'{self.__class__.__name__}: An empty list is put in "content".')
    
    def asType(self)->list[str]:
        list_json_str:list[str] = []
        list_json_str.append('{')
        if self.description is not None:
            list_json_str.append(f' "description":{self.json_literal(self.description)},')
        if self.nullable:
            list_json_str.append(' "type":["array", "null"],')
        else:
            list_json_str.append(' "type":"array",')

        if isinstance(self.content, JsonEntity):
            lines:list[str] = self.content.asType()
            lines[0] = '"items":'+lines[0]
            for single_line in lines:
                list_json_str.append(' '+single_line)
        elif isinstance(self.content, list) and isinstance(self.content[0], JsonEntity):
            list_json_str.append(' "items":{')
            list_json_str.append('  "oneOf":[')
            for entity in self.content:
                for single_line in entity.asType():
                    list_json_str.append('   '+single_line)
                list_json_str[-1] +=','
            list_json_str[-1]=list_json_str[-1].removesuffix(',')
            list_json_str.append('  ]')
            list_json_str.append(' }')
        else:
            raise TypeError(f'{self.__class__.__name__}: invalid "content" type')

        list_json_str.append('}')
        return list_json_str

    def as_dict(self) -> tuple[str, dict[str, Any]]:
        dict_this:dict = {}
        if self.description is not None:
            dict_this['description']=self.description
        if self.nullable:
            dict_this['type']=['array','null']
        else:
            dict_this['type']='array'

        if isinstance(self.content, JsonEntity):
            _, dict_given = self.content.as_dict()
            dict_this['items']=dict_given
            
        elif isinstance(self.content, list) and isinstance(self.content[0], JsonEntity):
            dict_oneof={'oneOf': [(single_content.as_dict())[1] for single_content in self.content]}
            dict_this['items']= dict_oneof
        else:
            raise TypeError(f'{self.__class__.__name__}: invalid "content" type')

        return (self.key, dict_this) 

    def asEntity(self)->list[str]:
        list_json_str:list[str] = self.asType()
        list_json_str[0] =f'{self.json_literal(self.key)}:'+list_json_str[0]
        return list_json_str

            
class Objason(JsonEntity):
    key_prop:str='peoperty'
    key_val:str='val'
    key_then:str = 'then'
    key_else:str = 'else'
    def __init__(self,
                key:str=None,
                props: list[JsonEntity]=None,
                description:str=None,
                required:bool=True,
                nullable:bool=False):
        super().__init__(key=key, description=description, required=required)
        self.nullable = nullable
        if key is None:
            raise ValueError(f'{self.__class__.__name__}: "key" not given.')  
        self.props=props
        if props is None or len(props)==0:
            raise ValueError(f'{self.__class__.__name__}: Property not given.')
        self.list_cond:list[dict[str,JsonEntity]] = []

    def asType(self)->list[str]:
        list_json_str: list[str] = []
        list_json_str.append('{')
        if self.description is not None:
            list_json_str.append(f' "description":{self.json_literal(self.description)},')
        if self.nullable:
            list_json_str.append(' "type":["object", "null"],')
        else:
            list_json_str.append(' "type":"object",')
        list_json_str.append(' "properties":{')
        required:str=''
        for single_prop in self.props:
            for line in single_prop.asEntity():
                list_json_str.append('  '+line)
            list_json_str[-1] += ','
            if single_prop.required:
                required += f'{self.json_literal(single_prop.key)},'
    
        list_json_str[-1]=list_json_str[-1].removesuffix(',')
        list_json_str.append(' },')

        required=required.removesuffix(',')
        if required != '':
            list_json_str.append(f' "required":[{required}],')
        
        if len(self.list_cond) > 0:
            self.__put_condition(list_json_str=list_json_str)
        list_json_str.append(' "additionalProperties":false')
        list_json_str.append('}')

        return list_json_str

    def as_dict(self)->tuple[str, dict[str, Any]]:
        def __put_condition_new():
            def then_else(dict_temp:dict = None, is_then:bool = True, cond: dict[str, JsonEntity]=None):
                # required:str = ''
                then_else:str = ''
                key_then_else:str = ''
                if is_then:
                    then_else = "then"
                    key_then_else = self.key_then
                else:
                    then_else = "else"
                    key_then_else = self.key_else
                
                if (list_prop_temp := cond[key_then_else]):
                    dict_temp[then_else]={
                        'required': [single_prop.key for single_prop in list_prop_temp]
                    }

            if 'allOf' not in dict_this:
                dict_this['allOf']=[]
                        
            for cond in self.list_cond:
                if isinstance(cond[self.key_val], list):
                    dict_temp= {
                                    'if':{
                                        'properties':{
                                            cond[self.key_prop]:{'enum':cond[self.key_val]}
                                        },
                                        'required': [cond[self.key_prop]]
                                    }
                                }
                elif cond[self.key_val] is not None:
                    dict_temp = {
                        'if':{
                            'properties':{
                                cond[self.key_prop]:{'const':cond[self.key_val]}
                            },
                            'required':[cond[self.key_prop]]
                        }
                    }
                else:
                    dict_temp = {
                        'if':{
                            'required':[cond[self.key_prop]]
                        }
                    }
                
                if cond[self.key_then] is not None and len(cond[self.key_then]) != 0:
                    then_else(dict_temp=dict_temp, is_then=True, cond=cond)
                if cond[self.key_else] is not None and len(cond[self.key_else]) != 0:
                    then_else(dict_temp=dict_temp, is_then=False, cond=cond)

                dict_this['allOf'].append(dict_temp)

        ##########################################################
        ##########################################################
        dict_this:dict={}

        if self.description is not None:
            dict_this['description'] = self.description
        if self.nullable:
            dict_this['type']=['object', 'null']
        else:
            dict_this['type']='object'

        dict_this['properties']={}
        for single_prop in self.props:
            name, json_dict = single_prop.as_dict()
            dict_this['properties'][name] = json_dict
        required = [p.key for p in self.props if p.required]
        if required:
            dict_this['required'] = required
        if len(self.list_cond) > 0:
            __put_condition_new()
        dict_this['additionalProperties']=False

        return (self.key, dict_this)

    def __put_condition(self, list_json_str: list[str]):
        def then_else(is_then:bool = True, cond: dict[str, JsonEntity]=None):
            required:str = ''
            then_else:str = ''
            key_then_else:str = ''
            if is_then:
                then_else = "then"
                key_then_else = self.key_then
            else:
                then_else = "else"
                key_then_else = self.key_else
            list_json_str.append(f'   "{then_else}":{{')
            list_prop_temp:list[JsonEntity] = cond[key_then_else]
            for single_prop in list_prop_temp:
                required += f'{self.json_literal(single_prop.key)},'
            required = required.removesuffix(',')
            if required != '':
                list_json_str.append(f'    "required":[{required}]')
            list_json_str.append('   },')

        list_json_str.append(' "allOf":[')
        for cond in self.list_cond:
            if isinstance(cond[self.key_val], list):
                temp_vals:str = ''
                for val in cond[self.key_val]:
                    temp_vals+=f'{self.json_literal(val)},'
                temp_vals=temp_vals.removesuffix(',')
                list_json_str.append('  {')
                list_json_str.append('   "if":{')
                list_json_str.append('    "properties":{')
                list_json_str.append(f'     "{cond[self.key_prop]}":{{"enum":[{temp_vals}]}}')
                list_json_str.append('    },')
                list_json_str.append(f'    "required":["{cond[self.key_prop]}"]')
                list_json_str.append('   },')
            elif cond[self.key_val] is not None:
                list_json_str.append('  {')
                list_json_str.append('   "if":{')
                list_json_str.append('    "properties":{')
                list_json_str.append(f'     "{cond[self.key_prop]}":{{"const":{self.json_literal(cond[self.key_val])}}}')
                list_json_str.append('    },')
                list_json_str.append(f'    "required":["{cond[self.key_prop]}"]')
                list_json_str.append('   },')
            else:
                list_json_str.append('  {')
                list_json_str.append('   "if":{')
                list_json_str.append(f'    "required":["{cond[self.key_prop]}"]')
                list_json_str.append('   },')
            if cond[self.key_then] is not None and len(cond[self.key_then]) != 0:
                then_else(is_then=True, cond=cond)
            if cond[self.key_else] is not None and len(cond[self.key_else]) != 0:
                then_else(is_then=False, cond=cond)
            list_json_str[-1] = list_json_str[-1].removesuffix(',')
            list_json_str.append('  },')
        list_json_str[-1] = list_json_str[-1].removesuffix(',')
        list_json_str.append(' ],')        



    
    def asEntity(self)->list[str]:
        list_json_str:list[str] = self.asType()
        list_json_str[0] =f'{self.json_literal(self.key)}:'+list_json_str[0]
        return list_json_str
    
    def if_then_else(self,
                     prop:str=None,
                     val_if:list[Any]|int|float|str=None,
                     props_then: list[JsonEntity]=[],
                     props_else: list[JsonEntity]=[]):
        temp_dict = {self.key_prop:prop,
                     self.key_val:val_if,
                     self.key_then:props_then,
                     self.key_else:props_else}
        self.list_cond.append(temp_dict)
        for temp_entry in (props_then+props_else):
            inclded_in_then_else:bool = False
            for prop_exist in self.props:
                if prop_exist.key == temp_entry.key:
                    inclded_in_then_else = True
                    continue
            if not inclded_in_then_else:
                temp_entry.required = False
                self.props.append(temp_entry)
      
        


        
class Primitive(JsonEntity):
    def __init__(self,
                 prim_type:Literal['string','integer', 'number','boolean']|list[Literal['string','integer', 'number','boolean']] = None,
                 key:str = None,
                 description:str = None,
                 enum:list[str]|list[int]|list[float]|list[bool] = None,
                 const:str|int|float|bool = None,
                 nullable:bool=False,
                 required:bool = True):
        super().__init__(key=key, description=description, required=required)
        self.prim_type:str|list[str] = prim_type
        self.enum:list[str]|list[int]|list[float]|list[bool] = enum
        self.const:str|int|float|bool = const
        self.nullable:bool = nullable
        if key is None:
            raise ValueError(f'{self.__class__.__name__}: "key" not given.')  
        if enum is not None and const is not None:
            raise ValueError(f'{self.__class__.__name__}: "enum" and "const" are given at the same time.')
        if prim_type is None:
            raise ValueError(f'{self.__class__.__name__}: Type not selected.')

    
    def asType(self)->list[str]:
        list_json_str: list[str] = []
        list_json_str.append('{')
        if self.description is not None:
            list_json_str.append(f' "description":{self.json_literal(self.description)},')
        if isinstance(self.prim_type, list):
            joined = ', '.join(f'"{item}"' for item in self.prim_type)
            if self.nullable:
                list_json_str.append(f' "type": [{joined}, "null"],')
            else:
                list_json_str.append(f' "type": [{joined}],')
        else:    
            if self.nullable:
                list_json_str.append(f' "type": ["{self.prim_type}", "null"],')
            else:
                list_json_str.append(f' "type":"{self.prim_type}",')

        if self.enum is not None:
            enum_values = ','.join(self.json_literal(item) for item in self.enum)
            if self.nullable:
                enum_values += ',null'
            list_json_str.append(f' "enum":[{enum_values}],')

        if self.const is not None:
            list_json_str.append(f' "const":{self.json_literal(self.const)},')

        list_json_str[-1]=list_json_str[-1].removesuffix(',')
        list_json_str.append('}')
        return list_json_str

    def as_dict(self)->tuple[str, dict[str,Any]]:
        dict_this:dict[str,Any]={}

        if self.description is not None:
            dict_this['description'] = self.description
        if isinstance(self.prim_type, list):   
            if self.nullable:
                dict_this['type'] = self.prim_type + ['null']
            else:
                dict_this['type'] = list(self.prim_type) #list() is for shallow copy
        else:
            if self.nullable:
                dict_this['type'] = [self.prim_type, 'null']
            else:
                dict_this['type'] = self.prim_type

        if self.enum is not None:
            if self.nullable:
                dict_this['enum']=self.enum+[None]
            else:
                dict_this['enum']= list(self.enum) #list() is for shallow copy

        if self.const is not None:
            dict_this['const']=self.const

        return (self.key, dict_this)
    
    def asEntity(self)->list[str]:
        list_json_str:list[str] = self.asType()
        list_json_str[0] =f'{self.json_literal(self.key)}:'+list_json_str[0]
        return list_json_str
    
            

class Tuple(JsonEntity):
    def __init__(self,
                 key:str = None,
                 content:list[JsonEntity]=None,
                 description:str = None,
                 required = True):
        super().__init__(key, description, required)
        self.content:list[JsonEntity] = content
        
        if key is None:
            raise ValueError(f'{self.__class__.__name__}: "key" not given.')        
        if self.content is None:
            raise ValueError(f'{self.__class__.__name__}: "content" not given.')
        if len(self.content) == 0:
            raise ValueError(f'{self.__class__.__name__}: An empty list is put in "content".')
        self.num_content:int = len(self.content)
        
    def asType(self)->list[str]:
        list_json_str:list[str]=[]
        list_json_str.append('{')
        if self.description is not None:
            list_json_str.append(f' "description":{self.json_literal(self.description)},')
        list_json_str.append(' "type":"array",')
        list_json_str.append(' "prefixItems": [')
        for entity in self.content:
            for single_line in entity.asType():
                list_json_str.append('  '+single_line)
            list_json_str[-1]+=','
        list_json_str[-1] = list_json_str[-1].removesuffix(',')
        list_json_str.append(' ],')
        list_json_str.append(' "items":false,')
        list_json_str.append(f' "minItems":{self.num_content},')
        list_json_str.append(f' "maxItems":{self.num_content}')
        list_json_str.append('}')
        return list_json_str
    
    def asEntity(self)->list[str]:
        list_json_str:list[str]=self.asType()
        list_json_str[0]=f'{self.json_literal(self.key)}:'+list_json_str[0]
        return list_json_str

    def as_dict(self)->tuple[str, dict[str, Any]]:
        dict_this:dict[str, Any]={}
    
        if self.description is not None:
            dict_this['description']=self.description
        dict_this['type']='array'
        dict_this['prefixItems'] = [entity.as_dict()[1] for entity in self.content]
        dict_this['items']=False
        dict_this['minItems']=self.num_content
        dict_this['maxItems']=self.num_content
        return (self.key, dict_this)
        


