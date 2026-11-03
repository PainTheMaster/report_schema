from report_schema import Paragraph, Table, Section, Chapter, Report
from typing import Any
import json


def strip_code_fence(text:str)->str:
    '''Removes a Markdown code fence (```json ... ```) around the JSON, which is often included when copying an LLM output.'''
    lines = text.strip().splitlines()
    if lines and lines[0].startswith('```'):
        lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
    return '\n'.join(lines)


def wait_for_report_json(file_name:str)->Any:
    '''Waits until the file exists and contains valid JSON, then returns the parsed data.'''
    while True:
        input(f"Please generate '{file_name}' to form the report. Press enter when ready.")
        try:
            # utf-8-sig also accepts a file saved with BOM (e.g. by Notepad).
            with open(file_name, mode='r', encoding='utf-8-sig') as f:
                text = f.read()
            return json.loads(strip_code_fence(text))
        except FileNotFoundError:
            print(f"'{file_name}' not found.")
        except json.JSONDecodeError as e:
            print(f"'{file_name}' is not valid JSON: {e}")




def main():
    report = Report(description='Sample report')

    # Chapter1
    ch1 = Chapter(key='ch1', title='Chapter 1', topic='Introduction')
    
    ## Section 1
    s1 = Section(key='s1', title='Section 1', topic='Overview')
    p1 = Paragraph(key='p1', topic='Why an egg is a perfect food.')
    p2 = Paragraph(key='p2', topic='Nutrients in an egg.')
    p3 = Paragraph(key='p3', topic='Example of traditional egg recipes.')
    p4 = Paragraph(key='p4', topic='A new egg dish is introduced in this report.')

    s1.add_component(p1)
    s1.add_component(p2)
    s1.add_component(p3)
    s1.add_component(p4)
    ch1.add_section(s1)
    report.add_chapter(ch1)

    # Chapter 2
    ch2 = Chapter(key='ch2', title='Chapter 2: Why breakthrough is needed', topic='Importance')
    s1 = Section(key='s1', title='Section 1', topic='Need')
    p1 = Paragraph(key='p1', topic='Current challenges.')
    p2 = Paragraph(key='p2', topic='Need for change.')
    p3 = Paragraph(key='p3', topic='Preceding studies.')
    s1.add_component(p1)
    s1.add_component(p2)
    s1.add_component(p3)


    s2 = Section(key='s2', title='Section 2', topic='Hypothesis')
    p1 = Paragraph(key='p1', topic='Proposed solution.')
    s2.add_component(p1)
    
    ch2.add_section(s1)
    ch2.add_section(s2)
    report.add_chapter(ch2)

    # Chapter 3
    ch3 = Chapter(key='ch3', title='Chapter 3: Results', topic='Results')
    s1 = Section(key='s1', title='Section 1', topic='Whole fried egg with shell')
    p1 = Paragraph(key='p1', topic='Cooking method of fried egg results.')
    p2 = Paragraph(key='p2', topic='Explosion')
    p3 = Paragraph(key='p3', topic='Loss of life')
    s1.add_component(p1)
    s1.add_component(p2)
    s1.add_component(p3)
    ch3.add_section(s1)

    s2 = Section(key='s2', title='Section 2', topic='Ultracentrifuged egg')
    p1 = Paragraph(key='p1', topic='Cooking method of the ultracentrifuged egg')
    p2 = Paragraph(key='p2', topic='Isotopical separation of atoms constituting the egg.')
    t2 = Table(key='t2', topic='Separation results.')
    p3 = Paragraph(key='p3', topic='Result (taste) of the dish.')
    p4 = Paragraph(key='p4', topic='Interference by the allied forces.')
    s2.add_component(p1)
    s2.add_component(p2)
    s2.add_component(t2)
    s2.add_component(p3)
    s2.add_component(p4)
    ch3.add_section(s2)

    report.add_chapter(ch3)

    # Chapter 4
    ch4 = Chapter(key='ch4', title='Chapter 4: Discussion', topic='Discussions about the results')
    s1 = Section(key='s1', title='Section 1: danger of deep frying eggs', topic='Safety')
    p1 = Paragraph(key='p1', topic='Phase change of water in an egg and thermodynamics')
    p2 = Paragraph(key='p2', topic='Risk assessment')
    p3 = Paragraph(key='p3', topic='Safety considerations')
    s1.add_component(p1)
    s1.add_component(p2)
    s1.add_component(p3)
    ch4.add_section(s1)

    s2 = Section(key='s2', title='Section 2: Ultracentrifuged egg', topic='Ultracentrifugation of eggs')
    p1 = Paragraph(key='p1', topic='Why this is the best egg cuisine ever!!!')
    p2 = Paragraph(key='p2', topic='Ethical aspect of centrifuging eggs.')
    p3 = Paragraph(key='p3', topic='What triggered the military operation of the allied forces?')
    p4 = Paragraph(key='p4', topic='Possible settlement and peace treaty.')
    
    s2.add_component(p1)
    s2.add_component(p2)
    s2.add_component(p3)
    s2.add_component(p4)
    ch4.add_section(s2) 
    report.add_chapter(ch4)

    # Chapter 5
    ch5 = Chapter(key='ch5', title='Chapter 5: Conclusion', topic='Conclusion')
    s1 = Section(key='s1', title='Summary', topic='Conclusion')
    p1 = Paragraph(key='p1', topic='Why I love eggs.')
    p2 = Paragraph(key='p2', topic='Summary of findings.')
    p3 = Paragraph(key='p3', topic='Ambitions for future work.')

    s1.add_component(p1)
    s1.add_component(p2)
    s1.add_component(p3)
    ch5.add_section(s1)
    report.add_chapter(ch5)

    with open('report_schema.json', mode='w', encoding='utf-8') as f:
        json.dump(report.get_schema(), f, ensure_ascii=False, indent=2)

    print("Report schema saved.")
    data = wait_for_report_json('report.json')

    report_output=report.compose(dict_data=data)

    print(report_output)



    




if __name__ == '__main__':
    main()

