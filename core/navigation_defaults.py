"""The site menu as it was built into the frontend (data/navigation.json),
with English and French labels. Used by `manage.py seed_navigation` to
fill Impostazioni → Navigazione once. Edit the menu in the CMS, not here."""

DEFAULT_MENU = [
    {
        "label": "Cosa monitoriamo?",
        "label_en": "What we monitor",
        "label_fr": "Ce que nous surveillons",
        "groups": [
            {
                "label": "Ambiente",
                "label_en": "Environment",
                "label_fr": "Environnement",
                "links": [
                    {
                        "label": "Alberi",
                        "label_en": "Trees",
                        "label_fr": "Arbres",
                        "href": "/monitoraggio/alberi"
                    },
                    {
                        "label": "Aria",
                        "label_en": "Air",
                        "label_fr": "Air",
                        "href": "/monitoraggio/aria"
                    },
                    {
                        "label": "Fiumi",
                        "label_en": "Rivers",
                        "label_fr": "Rivières",
                        "href": "/monitoraggio/fiumi"
                    },
                    {
                        "label": "Frane",
                        "label_en": "Landslides",
                        "label_fr": "Glissements de terrain",
                        "href": "/monitoraggio/frane"
                    }
                ]
            },
            {
                "label": "Viabilità",
                "label_en": "Roads",
                "label_fr": "Routes",
                "links": [
                    {
                        "label": "Traffico",
                        "label_en": "Traffic",
                        "label_fr": "Trafic",
                        "href": "/monitoraggio/traffico"
                    },
                    {
                        "label": "Cantieri",
                        "label_en": "Road works",
                        "label_fr": "Chantiers",
                        "href": "/monitoraggio/cantieri"
                    },
                    {
                        "label": "Gallerie",
                        "label_en": "Tunnels",
                        "label_fr": "Tunnels",
                        "href": "/monitoraggio/gallerie"
                    }
                ]
            },
            {
                "label": "Strutture",
                "label_en": "Structures",
                "label_fr": "Ouvrages",
                "links": [
                    {
                        "label": "Ponti",
                        "label_en": "Bridges",
                        "label_fr": "Ponts",
                        "href": "/monitoraggio/ponti"
                    },
                    {
                        "label": "Edifici",
                        "label_en": "Buildings",
                        "label_fr": "Bâtiments",
                        "href": "/monitoraggio/edifici"
                    }
                ]
            }
        ]
    },
    {
        "label": "Come lo realizziamo?",
        "label_en": "How we do it",
        "label_fr": "Comment nous le faisons",
        "groups": [
            {
                "label": "Piattaforme",
                "label_en": "Platforms",
                "label_fr": "Plateformes",
                "links": [
                    {
                        "label": "Gestionale AngelBPM",
                        "label_en": "AngelBPM platform",
                        "label_fr": "Plateforme AngelBPM",
                        "href": "/soluzioni/angel-bpm"
                    },
                    {
                        "label": "Analitici",
                        "label_en": "Analytics",
                        "label_fr": "Analytique",
                        "href": "/soluzioni/analitici"
                    }
                ]
            },
            {
                "label": "Sensori",
                "label_en": "Sensors",
                "label_fr": "Capteurs",
                "links": [
                    {
                        "label": "Sensori",
                        "label_en": "Sensors",
                        "label_fr": "Capteurs",
                        "href": "/soluzioni/sensori"
                    },
                    {
                        "label": "Telecamere intelligenti",
                        "label_en": "Smart cameras",
                        "label_fr": "Caméras intelligentes",
                        "href": "/soluzioni/telecamere-intelligenti"
                    }
                ]
            },
            {
                "label": "Tecnologie",
                "label_en": "Technologies",
                "label_fr": "Technologies",
                "links": [
                    {
                        "label": "LoRaWAN",
                        "label_en": "LoRaWAN",
                        "label_fr": "LoRaWAN",
                        "href": "/soluzioni/lorawan"
                    },
                    {
                        "label": "Networking",
                        "label_en": "Networking",
                        "label_fr": "Réseaux",
                        "href": "/soluzioni/networking"
                    },
                    {
                        "label": "Firmware",
                        "label_en": "Firmware",
                        "label_fr": "Firmware",
                        "href": "/soluzioni/firmware"
                    },
                    {
                        "label": "SCADA",
                        "label_en": "SCADA",
                        "label_fr": "SCADA",
                        "href": "/soluzioni/scada"
                    },
                    {
                        "label": "PLC",
                        "label_en": "PLC",
                        "label_fr": "Automates (PLC)",
                        "href": "/soluzioni/plc"
                    }
                ]
            },
            {
                "label": "Servizi",
                "label_en": "Services",
                "label_fr": "Services",
                "links": [
                    {
                        "label": "Progettazione",
                        "label_en": "Design",
                        "label_fr": "Conception",
                        "href": "/soluzioni/progettazione"
                    },
                    {
                        "label": "Direzione lavori",
                        "label_en": "Works supervision",
                        "label_fr": "Direction des travaux",
                        "href": "/soluzioni/direzione-lavori"
                    },
                    {
                        "label": "Control Room",
                        "label_en": "Control room",
                        "label_fr": "Salle de contrôle",
                        "href": "/soluzioni/control-room"
                    }
                ]
            }
        ]
    },
    {
        "label": "Prodotti",
        "label_en": "Products",
        "label_fr": "Produits",
        "href": "/prodotti",
        "groups": []
    },
    {
        "label": "Casi di successo",
        "label_en": "Success stories",
        "label_fr": "Réussites",
        "href": "/casi",
        "groups": []
    },
    {
        "label": "Approfondimenti",
        "label_en": "Insights",
        "label_fr": "Ressources",
        "groups": [
            {
                "label": "Risorse",
                "label_en": "Resources",
                "label_fr": "Ressources",
                "links": [
                    {
                        "label": "News",
                        "label_en": "News",
                        "label_fr": "Actualités",
                        "href": "/news"
                    },
                    {
                        "label": "Academy",
                        "label_en": "Academy",
                        "label_fr": "Académie",
                        "href": "/approfondimenti/academy"
                    },
                    {
                        "label": "FAQ",
                        "label_en": "FAQ",
                        "label_fr": "FAQ",
                        "href": "/approfondimenti/faq"
                    },
                    {
                        "label": "Glossario",
                        "label_en": "Glossary",
                        "label_fr": "Glossaire",
                        "href": "/approfondimenti/glossario"
                    }
                ]
            }
        ]
    },
    {
        "label": "Azienda",
        "label_en": "Company",
        "label_fr": "Entreprise",
        "groups": [
            {
                "label": "Axatel",
                "label_en": "Axatel",
                "label_fr": "Axatel",
                "links": [
                    {
                        "label": "Chi siamo?",
                        "label_en": "About us",
                        "label_fr": "Qui sommes-nous ?",
                        "href": "/azienda/chi-siamo"
                    },
                    {
                        "label": "Team",
                        "label_en": "Team",
                        "label_fr": "Équipe",
                        "href": "/azienda/team"
                    },
                    {
                        "label": "Bilancio di sostenibilità",
                        "label_en": "Sustainability report",
                        "label_fr": "Rapport de durabilité",
                        "href": "/azienda/bilancio-sostenibilita"
                    }
                ]
            },
            {
                "label": "Lavora con noi",
                "label_en": "Work with us",
                "label_fr": "Travailler avec nous",
                "links": [
                    {
                        "label": "Invia il CV",
                        "label_en": "Send your CV",
                        "label_fr": "Envoyer votre CV",
                        "href": "/azienda/invia-il-cv"
                    },
                    {
                        "label": "Diventa Partner",
                        "label_en": "Become a partner",
                        "label_fr": "Devenir partenaire",
                        "href": "/azienda/diventa-partner"
                    }
                ]
            },
            {
                "label": "Contatti",
                "label_en": "Contact",
                "label_fr": "Contact",
                "links": [
                    {
                        "label": "Parla con noi",
                        "label_en": "Talk to us",
                        "label_fr": "Parlez-nous",
                        "href": "/contatti"
                    }
                ]
            }
        ]
    }
]
