{
    "name": "Recursos Humanos Herrera C.A",
    "version": "1.1",
    "author" : "Herrera C.A",
    "category": "RRHH",
    "description": """
     Este modulo contiene las adaptaciones del modulo de recursos humanos para HERRERA, C.A
    """,
    'images': [],
    'depends': ['hr', 'sale'],
    'data': ['data/hr_department.xml','data/job_data.xml', 'data/employee_data.xml'],
    'init_xml': [],
    'update_xml': ['view/hr_view.xml'],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': True,
    'auto_install': False,
}
