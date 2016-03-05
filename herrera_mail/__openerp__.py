{
    "name" : "Mensajeria Herrera",
    "version": "1.0",
    "depends" : ["base", "mail", "portal"],
    "author" : "Herrera C.A.",
    "description" : """
    ¿Que hace este módulo?:

        Este módulo es una herencia de Mail OpenERP

			""",
    "website" : "http://www.herrera.com.ve",
    "category" : "Mail",
    "init_xml" : [],
    "demo_xml" : [    ],
    "test": [],
    "data" : [
                'data/sequence_data.xml',
                'data/mail_auth_data.xml',
                'view/mail_view.xml',
                'wizard/mail_compose_message_view.xml',
    ],
    "active": False,
    "installable": True,
}
