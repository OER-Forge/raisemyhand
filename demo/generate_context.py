#!/usr/bin/env python3
"""
Generate realistic demo context JSON files for a specific STEM course.

This script creates JSON files for:
- Instructors (with realistic names, emails, credentials)
- Classes (course descriptions, metadata)
- Class Meetings (lecture sessions with topics)
- Questions (realistic student questions for each meeting)
- System Config (optional feature flags)

Usage:
    python demo/generate_context.py --context physics_101 --manual
    python demo/generate_context.py --context biology_200 --llm-api

The --manual flag uses predefined templates.
The --llm-api flag would call an LLM API (requires separate implementation).
"""
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
import random
import string


class DemoContextGenerator:
    """Generate realistic demo context for STEM courses."""
    
    # Predefined contexts with course metadata
    CONTEXTS = {
        "physics_101": {
            "title": "Physics 101: Classical Mechanics",
            "department": "Physics",
            "level": "undergraduate",
            "semester": "Fall 2025",
            "instructors": [
                {
                    "first_name": "Sarah",
                    "last_name": "Einstein",
                    "title": "Dr.",
                    "specialization": "Classical Mechanics"
                },
                {
                    "first_name": "James",
                    "last_name": "Maxwell",
                    "title": "Prof.",
                    "specialization": "Electromagnetism"
                }
            ],
            "topics": [
                {
                    "title": "Introduction to Kinematics",
                    "description": "Position, velocity, acceleration in 1D and 2D",
                    "day": 1
                },
                {
                    "title": "Newton's Laws of Motion",
                    "description": "Three laws and their applications",
                    "day": 3
                },
                {
                    "title": "Work, Energy, and Power",
                    "description": "Conservation of energy, kinetic and potential energy",
                    "day": 5
                },
                {
                    "title": "Linear Momentum and Collisions",
                    "description": "Impulse, elastic and inelastic collisions",
                    "day": 8
                },
                {
                    "title": "Rotational Motion",
                    "description": "Angular velocity, torque, moment of inertia",
                    "day": 10
                }
            ],
            "questions_per_topic": [
                # Day 1: Introduction to Kinematics
                [
                    "How do we distinguish between distance and displacement?",
                    "Can velocity be negative? What does that mean physically?",
                    "What's the difference between average and instantaneous velocity?",
                    "How do we interpret position-time graphs?",
                    "When is acceleration zero but velocity non-zero?",
                    "How do we calculate displacement from a velocity-time graph?",
                    "What are the units for acceleration and why?",
                    "Can an object have zero velocity but non-zero acceleration?",
                    "How do we handle 2D motion vs 1D motion?",
                    "What's the significance of the slope in a velocity-time graph?",
                    "How do we apply kinematic equations to real-world problems?",
                    "What assumptions do we make when using kinematic equations?"
                ],
                # Day 3: Newton's Laws
                [
                    "How does Newton's third law apply to rocket propulsion?",
                    "What's the difference between mass and weight?",
                    "How do we identify all forces acting on an object?",
                    "When can we treat friction as negligible?",
                    "How does normal force relate to weight on an incline?",
                    "What's the relationship between force and acceleration?",
                    "How do action-reaction pairs work in connected objects?",
                    "Can we have motion without a net force?",
                    "How do we solve problems with multiple forces at angles?",
                    "What's the role of free body diagrams in problem solving?",
                    "How does air resistance affect falling objects?",
                    "What's the difference between static and kinetic friction?"
                ],
                # Day 5: Work, Energy, Power
                [
                    "How is work different from effort in physics?",
                    "Can work be negative? When does that happen?",
                    "What's the relationship between work and kinetic energy?",
                    "How do we apply conservation of energy to real problems?",
                    "What's the difference between conservative and non-conservative forces?",
                    "How do we calculate potential energy for different systems?",
                    "What's power and how does it relate to work?",
                    "How do we account for energy losses in real systems?",
                    "Can total mechanical energy increase in a system?",
                    "How do springs store and release energy?",
                    "What's the work-energy theorem and when do we use it?",
                    "How do we handle multi-step energy transformation problems?"
                ],
                # Day 8: Momentum and Collisions
                [
                    "How is momentum different from velocity?",
                    "Why is momentum conserved but kinetic energy sometimes isn't?",
                    "How do we analyze two-dimensional collisions?",
                    "What's the difference between elastic and inelastic collisions?",
                    "How does impulse relate to change in momentum?",
                    "Can momentum be conserved if external forces are present?",
                    "How do we calculate final velocities in collisions?",
                    "What's the center of mass and why is it important?",
                    "How do crumple zones in cars relate to impulse?",
                    "Can we have a perfectly inelastic collision?",
                    "How do we solve collision problems with different masses?",
                    "What happens to energy in inelastic collisions?"
                ],
                # Day 10: Rotational Motion
                [
                    "How is angular velocity different from linear velocity?",
                    "What's moment of inertia and how do we calculate it?",
                    "How does torque cause rotational motion?",
                    "What's the rotational equivalent of Newton's second law?",
                    "How do we calculate rotational kinetic energy?",
                    "What's the relationship between torque and angular acceleration?",
                    "How do we handle problems with both linear and rotational motion?",
                    "What's angular momentum and when is it conserved?",
                    "How do we calculate the moment of inertia for complex shapes?",
                    "What's the parallel axis theorem?",
                    "How does rolling motion combine translation and rotation?",
                    "Why do figure skaters spin faster when they pull their arms in?"
                ]
            ]
        },
        "biology_200": {
            "title": "Biology 200: Cell Biology and Genetics",
            "department": "Biology",
            "level": "undergraduate",
            "semester": "Fall 2025",
            "instructors": [
                {
                    "first_name": "Rachel",
                    "last_name": "Carson",
                    "title": "Dr.",
                    "specialization": "Cell Biology"
                }
            ],
            "topics": [
                {
                    "title": "Cell Structure and Function",
                    "description": "Organelles, membranes, and cellular processes",
                    "day": 1
                },
                {
                    "title": "DNA Replication and Repair",
                    "description": "Molecular mechanisms of DNA replication",
                    "day": 4
                },
                {
                    "title": "Gene Expression and Regulation",
                    "description": "Transcription, translation, and gene regulation",
                    "day": 7
                },
                {
                    "title": "Mendelian Genetics",
                    "description": "Inheritance patterns and genetic crosses",
                    "day": 10
                },
                {
                    "title": "Cell Division: Mitosis and Meiosis",
                    "description": "Cell cycle, chromosome segregation",
                    "day": 13
                }
            ],
            "questions_per_topic": [
                # Day 1: Cell Structure
                [
                    "What's the difference between prokaryotic and eukaryotic cells?",
                    "How does the structure of mitochondria relate to their function?",
                    "What's the role of the endoplasmic reticulum in protein synthesis?",
                    "How do cells maintain selective permeability?",
                    "What's the function of the Golgi apparatus?",
                    "How do lysosomes contribute to cellular digestion?",
                    "What's the difference between smooth and rough ER?",
                    "How does the cytoskeleton provide cell structure?",
                    "What's the role of the nucleus in cellular function?",
                    "How do chloroplasts and mitochondria differ in function?",
                    "What are the components of the cell membrane?",
                    "How do cells communicate with each other?"
                ],
                # Day 4: DNA Replication
                [
                    "How does DNA polymerase add nucleotides?",
                    "What's the role of helicase in DNA replication?",
                    "Why is DNA replication semi-conservative?",
                    "How do cells correct errors during DNA replication?",
                    "What's the difference between leading and lagging strands?",
                    "What are Okazaki fragments and why do they form?",
                    "How does DNA ligase function in replication?",
                    "What's the role of primase in initiating replication?",
                    "How do telomeres protect chromosome ends?",
                    "What happens when DNA repair mechanisms fail?",
                    "How does DNA replication differ in prokaryotes and eukaryotes?",
                    "What's the proofreading function of DNA polymerase?"
                ],
                # Day 7: Gene Expression
                [
                    "How does transcription differ from translation?",
                    "What's the role of RNA polymerase in gene expression?",
                    "How do ribosomes read mRNA codons?",
                    "What's alternative splicing and why is it important?",
                    "How do transcription factors regulate gene expression?",
                    "What's the function of tRNA in translation?",
                    "How does the genetic code work?",
                    "What's the difference between introns and exons?",
                    "How do cells regulate when genes are expressed?",
                    "What's post-transcriptional modification?",
                    "How do enhancers and promoters differ?",
                    "What's epigenetic regulation of gene expression?"
                ],
                # Day 10: Mendelian Genetics
                [
                    "What's the difference between genotype and phenotype?",
                    "How do we use Punnett squares to predict offspring?",
                    "What's the law of segregation?",
                    "How does independent assortment work?",
                    "What's the difference between dominant and recessive alleles?",
                    "How do we calculate probability in genetic crosses?",
                    "What's incomplete dominance vs codominance?",
                    "How do multiple alleles affect inheritance?",
                    "What's a test cross and when do we use it?",
                    "How do linked genes violate independent assortment?",
                    "What's the difference between homozygous and heterozygous?",
                    "How do we determine if a trait is sex-linked?"
                ],
                # Day 13: Cell Division
                [
                    "What's the difference between mitosis and meiosis?",
                    "How does the cell cycle regulate cell division?",
                    "What happens during each phase of mitosis?",
                    "Why is meiosis necessary for sexual reproduction?",
                    "How do checkpoints prevent errors in cell division?",
                    "What's crossing over and when does it occur?",
                    "How does cytokinesis differ in plant and animal cells?",
                    "What's the role of spindle fibers in chromosome segregation?",
                    "How does meiosis create genetic diversity?",
                    "What happens when cell cycle regulation fails?",
                    "How many chromosomes are in human cells after mitosis vs meiosis?",
                    "What's the difference between sister chromatids and homologous chromosomes?"
                ]
            ]
        },
        "calculus_150": {
            "title": "Calculus 150: Differential Calculus",
            "department": "Mathematics",
            "level": "undergraduate",
            "semester": "Fall 2025",
            "instructors": [
                {
                    "first_name": "Isaac",
                    "last_name": "Newton",
                    "title": "Prof.",
                    "specialization": "Calculus"
                }
            ],
            "topics": [
                {
                    "title": "Limits and Continuity",
                    "description": "Concept of limits, limit laws, continuity",
                    "day": 1
                },
                {
                    "title": "The Derivative",
                    "description": "Definition, interpretation, basic rules",
                    "day": 4
                },
                {
                    "title": "Differentiation Rules",
                    "description": "Product rule, quotient rule, chain rule",
                    "day": 7
                },
                {
                    "title": "Applications of Derivatives",
                    "description": "Optimization, related rates, curve sketching",
                    "day": 10
                },
                {
                    "title": "Implicit Differentiation and Related Rates",
                    "description": "Techniques for implicit functions",
                    "day": 13
                }
            ],
            "questions_per_topic": [
                # Day 1: Limits
                [
                    "How do we evaluate limits algebraically?",
                    "What does it mean for a function to be continuous?",
                    "When do limits not exist?",
                    "How do we handle indeterminate forms like 0/0?",
                    "What's the difference between one-sided and two-sided limits?",
                    "How do we use the squeeze theorem?",
                    "What's the formal epsilon-delta definition of a limit?",
                    "How do limits at infinity work?",
                    "What's the intermediate value theorem?",
                    "How do we identify discontinuities?",
                    "When can we use direct substitution for limits?",
                    "How do rational functions behave at vertical asymptotes?"
                ],
                # Day 4: The Derivative
                [
                    "What's the geometric interpretation of the derivative?",
                    "How does the derivative relate to instantaneous rate of change?",
                    "What's the difference between average and instantaneous rate?",
                    "How do we use the limit definition to find derivatives?",
                    "When is a function not differentiable?",
                    "What's the relationship between continuity and differentiability?",
                    "How do we interpret negative derivatives?",
                    "What does the second derivative tell us?",
                    "How do we find the equation of a tangent line?",
                    "What's the derivative of a constant function?",
                    "How do derivatives apply to real-world problems?",
                    "What's the difference between f'(x) and dy/dx notation?"
                ],
                # Day 7: Differentiation Rules
                [
                    "How does the product rule work and why?",
                    "When do we use the quotient rule?",
                    "What's the chain rule and how do we apply it?",
                    "How do we differentiate composite functions?",
                    "What's the power rule for derivatives?",
                    "How do we handle nested function compositions?",
                    "What are the derivatives of trigonometric functions?",
                    "How do we differentiate exponential and logarithmic functions?",
                    "When do we need to use multiple rules together?",
                    "How do we differentiate inverse functions?",
                    "What's implicit vs explicit differentiation?",
                    "How do we verify our derivative calculations?"
                ],
                # Day 10: Applications
                [
                    "How do we find maximum and minimum values?",
                    "What's the first derivative test?",
                    "How do we determine intervals of increase/decrease?",
                    "What's concavity and how do we find inflection points?",
                    "How do we solve optimization problems?",
                    "What's the second derivative test for extrema?",
                    "How do we sketch curves using derivative information?",
                    "What are critical points and how do we find them?",
                    "How do we solve applied optimization problems?",
                    "What's the mean value theorem?",
                    "How do we identify absolute vs relative extrema?",
                    "How do asymptotes relate to curve sketching?"
                ],
                # Day 13: Implicit Differentiation
                [
                    "How do we differentiate implicit equations?",
                    "What's the difference between explicit and implicit functions?",
                    "How do we find dy/dx when y is not isolated?",
                    "What are related rates problems?",
                    "How do we set up related rates equations?",
                    "When do we use implicit differentiation?",
                    "How do we find the slope of implicitly defined curves?",
                    "What's the technique for differentiating both sides?",
                    "How do we solve for dy/dx in implicit equations?",
                    "How do related rates apply to real-world scenarios?",
                    "What's the strategy for word problems in related rates?",
                    "How do we verify implicit differentiation solutions?"
                ]
            ]
        },
        "chemistry_110": {
            "title": "Chemistry 110: General Chemistry I",
            "department": "Chemistry",
            "level": "undergraduate",
            "semester": "Fall 2025",
            "instructors": [
                {
                    "first_name": "Marie",
                    "last_name": "Curie",
                    "title": "Dr.",
                    "specialization": "Inorganic Chemistry"
                }
            ],
            "topics": [
                {
                    "title": "Atomic Structure and Periodicity",
                    "description": "Quantum mechanics, electron configuration, periodic trends",
                    "day": 1
                },
                {
                    "title": "Chemical Bonding",
                    "description": "Ionic, covalent, and metallic bonds",
                    "day": 5
                },
                {
                    "title": "Molecular Geometry and VSEPR",
                    "description": "Lewis structures, molecular shapes, polarity",
                    "day": 8
                },
                {
                    "title": "Stoichiometry and Chemical Reactions",
                    "description": "Balancing equations, mole calculations",
                    "day": 11
                },
                {
                    "title": "Thermochemistry",
                    "description": "Energy changes, enthalpy, calorimetry",
                    "day": 14
                }
            ],
            "questions_per_topic": [
                # Day 1: Atomic Structure
                [
                    "What's the difference between orbitals and electron shells?",
                    "How do we write electron configurations?",
                    "What are quantum numbers and what do they represent?",
                    "How does the aufbau principle work?",
                    "What's Hund's rule and why is it important?",
                    "How do we predict periodic trends like electronegativity?",
                    "What's the difference between valence and core electrons?",
                    "How does atomic radius change across the periodic table?",
                    "What's ionization energy and how does it vary?",
                    "How do we explain the wave-particle duality of electrons?",
                    "What's electron affinity?",
                    "How do electron configurations relate to chemical properties?"
                ],
                # Day 5: Chemical Bonding
                [
                    "What's the difference between ionic and covalent bonds?",
                    "How do we determine bond polarity?",
                    "What's electronegativity and how does it affect bonding?",
                    "How do we predict if a bond is ionic or covalent?",
                    "What are polar covalent bonds?",
                    "How does lattice energy relate to ionic compounds?",
                    "What's the octet rule and when does it apply?",
                    "How do coordinate covalent bonds form?",
                    "What's bond order and how do we calculate it?",
                    "How do metallic bonds differ from other bond types?",
                    "What are resonance structures?",
                    "How do we calculate formal charge?"
                ],
                # Day 8: Molecular Geometry
                [
                    "How do we use VSEPR theory to predict shapes?",
                    "What's the difference between electron geometry and molecular geometry?",
                    "How do lone pairs affect molecular shape?",
                    "How do we draw Lewis structures?",
                    "What determines if a molecule is polar?",
                    "How many electron groups correspond to each geometry?",
                    "What's the bond angle in different molecular shapes?",
                    "How do we identify hybridization of atoms?",
                    "What's the relationship between structure and polarity?",
                    "How do we handle molecules with multiple central atoms?",
                    "What's the difference between trigonal planar and tetrahedral?",
                    "How do double and triple bonds affect geometry?"
                ],
                # Day 11: Stoichiometry
                [
                    "How do we balance chemical equations?",
                    "What's the mole concept and why is it useful?",
                    "How do we calculate molar mass?",
                    "What's the limiting reagent in a reaction?",
                    "How do we determine percent yield?",
                    "What's the difference between empirical and molecular formulas?",
                    "How do we convert between moles, grams, and particles?",
                    "What's Avogadro's number and what does it represent?",
                    "How do we calculate theoretical yield?",
                    "What are stoichiometric coefficients?",
                    "How do we solve problems with excess reagent?",
                    "What's percent composition by mass?"
                ],
                # Day 14: Thermochemistry
                [
                    "What's the difference between heat and temperature?",
                    "How do we calculate enthalpy changes?",
                    "What's Hess's law and how do we use it?",
                    "How does calorimetry measure heat transfer?",
                    "What's the difference between exothermic and endothermic?",
                    "How do we use standard enthalpies of formation?",
                    "What's specific heat capacity?",
                    "How do we calculate heat absorbed or released?",
                    "What's the first law of thermodynamics?",
                    "How do bond energies relate to reaction enthalpy?",
                    "What's the difference between ΔH and ΔE?",
                    "How do we interpret thermochemical equations?"
                ]
            ]
        },
        "computer_science_101": {
            "title": "Computer Science 101: Introduction to Programming",
            "department": "Computer Science",
            "level": "undergraduate",
            "semester": "Fall 2025",
            "instructors": [
                {
                    "first_name": "Ada",
                    "last_name": "Lovelace",
                    "title": "Prof.",
                    "specialization": "Programming Languages"
                }
            ],
            "topics": [
                {
                    "title": "Variables, Data Types, and Operators",
                    "description": "Basic programming concepts and syntax",
                    "day": 1
                },
                {
                    "title": "Control Flow: Conditionals and Loops",
                    "description": "If statements, for loops, while loops",
                    "day": 4
                },
                {
                    "title": "Functions and Modularity",
                    "description": "Function definition, parameters, return values",
                    "day": 7
                },
                {
                    "title": "Lists and Data Structures",
                    "description": "Arrays, lists, dictionaries, tuples",
                    "day": 10
                },
                {
                    "title": "File I/O and Exception Handling",
                    "description": "Reading/writing files, error handling",
                    "day": 13
                }
            ],
            "questions_per_topic": [
                # Day 1: Variables and Data Types
                [
                    "What's the difference between integers and floats?",
                    "How do we name variables following best practices?",
                    "What's type conversion and when do we need it?",
                    "How do strings differ from numeric types?",
                    "What's the difference between = and ==?",
                    "How do we concatenate strings?",
                    "What's the order of operations for arithmetic operators?",
                    "How do boolean values work in Python?",
                    "What's the difference between mutable and immutable types?",
                    "How do we format output with print statements?",
                    "What's variable scope?",
                    "How do we handle user input?"
                ],
                # Day 4: Control Flow
                [
                    "How does an if-elif-else chain work?",
                    "What's the difference between for and while loops?",
                    "When should we use break vs continue?",
                    "How do we nest conditional statements?",
                    "What's the range() function and how do we use it?",
                    "How do logical operators (and, or, not) work?",
                    "What's an infinite loop and how do we avoid it?",
                    "How do we iterate over strings?",
                    "What's the difference between < and <=?",
                    "How do we create complex boolean conditions?",
                    "What happens if multiple conditions are true?",
                    "How do we use loops for input validation?"
                ],
                # Day 7: Functions
                [
                    "What's the difference between parameters and arguments?",
                    "How do return values work?",
                    "What happens when a function doesn't have a return statement?",
                    "How do we call functions from other functions?",
                    "What's function scope vs global scope?",
                    "How do default parameters work?",
                    "What are keyword arguments?",
                    "How do we document functions with docstrings?",
                    "What's the difference between print and return?",
                    "How do we pass lists to functions?",
                    "What's recursion and when do we use it?",
                    "How do we test functions effectively?"
                ],
                # Day 10: Lists and Data Structures
                [
                    "How do we access list elements by index?",
                    "What's list slicing and how does it work?",
                    "How do we add and remove items from lists?",
                    "What's the difference between lists and tuples?",
                    "How do dictionaries work with key-value pairs?",
                    "How do we iterate over lists?",
                    "What are list comprehensions?",
                    "How do we sort and search lists?",
                    "What's the difference between append and extend?",
                    "How do nested lists work?",
                    "How do we check if an item is in a list?",
                    "What are common list methods?"
                ],
                # Day 13: File I/O
                [
                    "How do we open and close files in Python?",
                    "What's the difference between read(), readline(), and readlines()?",
                    "How do we write data to a file?",
                    "What's the 'with' statement and why use it?",
                    "How do we handle file paths?",
                    "What's the difference between 'r', 'w', and 'a' modes?",
                    "How do we read CSV files?",
                    "What are exceptions and how do we catch them?",
                    "How does try-except-finally work?",
                    "What happens if a file doesn't exist?",
                    "How do we process large files efficiently?",
                    "How do we handle different file encodings?"
                ]
            ]
        }
    }
    
    def __init__(self, context_name: str, output_dir: Path):
        if context_name not in self.CONTEXTS:
            raise ValueError(f"Unknown context: {context_name}. Available: {list(self.CONTEXTS.keys())}")
        
        self.context_name = context_name
        self.context = self.CONTEXTS[context_name]
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track IDs for relationships
        self.semester_start = datetime(2025, 1, 13)  # Monday, Jan 13, 2025
    
    def generate_meeting_code(self) -> str:
        """Generate random meeting code."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    
    def generate_instructors_json(self):
        """Generate instructors.json file."""
        instructors = []
        
        for idx, inst_data in enumerate(self.context["instructors"], 1):
            username = f"{inst_data['first_name'].lower()}_{inst_data['last_name'].lower()}"
            email = f"{inst_data['first_name'].lower()}.{inst_data['last_name'].lower()}@university.edu"
            
            instructors.append({
                "username": username,
                "email": email,
                "display_name": f"{inst_data['title']} {inst_data['first_name']} {inst_data['last_name']}",
                "password": "demo123",  # Default demo password
                "role": "INSTRUCTOR",
                "is_active": True,
                "created_at": (self.semester_start - timedelta(days=30)).isoformat(),
                "api_key": APIKey.generate_key() if idx == 1 else APIKey.generate_key(),
                "api_key_name": f"{inst_data['first_name']}'s Demo API Key",
                "specialization": inst_data.get("specialization", "")
            })
        
        output = {"instructors": instructors}
        
        filepath = self.output_dir / "instructors.json"
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✓ Generated instructors.json with {len(instructors)} instructors")
        return instructors
    
    def generate_classes_json(self, instructors):
        """Generate classes.json file."""
        classes = []
        
        # Main class taught by first instructor
        instructor = instructors[0]
        classes.append({
            "class_id": f"{self.context_name}_main",
            "instructor_username": instructor["username"],
            "name": self.context["title"],
            "description": f"{self.context['semester']} section of {self.context['title']}. "
                          f"This course explores fundamental concepts in {self.context['department']}.",
            "created_at": (self.semester_start - timedelta(days=20)).isoformat(),
            "is_archived": False
        })
        
        output = {"classes": classes}
        
        filepath = self.output_dir / "classes.json"
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✓ Generated classes.json with {len(classes)} classes")
        return classes
    
    def generate_meetings_json(self, instructors, classes):
        """Generate meetings.json file."""
        meetings = []
        
        instructor = instructors[0]
        class_data = classes[0]
        
        for idx, topic in enumerate(self.context["topics"], 1):
            meeting_date = self.semester_start + timedelta(days=topic["day"] - 1)
            
            meetings.append({
                "meeting_id": f"{self.context_name}_day{topic['day']}",
                "class_id": class_data["class_id"],
                "instructor_username": instructor["username"],
                "meeting_code": self.generate_meeting_code(),
                "instructor_code": self.generate_meeting_code(),
                "title": f"Day {topic['day']}: {topic['title']}",
                "description": topic["description"],
                "password": None,  # No password for demo
                "created_at": meeting_date.replace(hour=9, minute=0).isoformat(),
                "started_at": meeting_date.replace(hour=10, minute=0).isoformat(),
                "is_active": idx <= 2,  # First 2 meetings active, rest ended
                "ended_at": None if idx <= 2 else meeting_date.replace(hour=11, minute=30).isoformat()
            })
        
        output = {"meetings": meetings}
        
        filepath = self.output_dir / "meetings.json"
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✓ Generated meetings.json with {len(meetings)} meetings")
        return meetings
    
    def generate_questions_json(self, meetings):
        """Generate questions.json file."""
        all_questions = []
        question_global_id = 1
        
        for meeting_idx, meeting in enumerate(meetings):
            topic_questions = self.context["questions_per_topic"][meeting_idx]
            
            # Select 10-15 questions randomly from the topic
            num_questions = random.randint(10, min(15, len(topic_questions)))
            selected_questions = random.sample(topic_questions, num_questions)
            
            meeting_date = datetime.fromisoformat(meeting["started_at"])
            
            for q_num, question_text in enumerate(selected_questions, 1):
                # Questions arrive during the 90-minute session
                question_time = meeting_date + timedelta(minutes=random.randint(5, 85))
                
                # Generate realistic vote patterns
                # Popular questions: 8-20 votes, Medium: 3-7, Low: 0-2
                vote_tier = random.choices(['popular', 'medium', 'low'], weights=[0.2, 0.5, 0.3])[0]
                
                if vote_tier == 'popular':
                    num_votes = random.randint(8, 20)
                elif vote_tier == 'medium':
                    num_votes = random.randint(3, 7)
                else:
                    num_votes = random.randint(0, 2)
                
                # Generate unique student voters (prevent duplicate constraint violations)
                votes = []
                voted_students = set()
                for v in range(num_votes):
                    # Get a unique student to vote (no duplicates per question)
                    attempts = 0
                    while attempts < 120:  # Max number of students
                        student_id = f"student_{random.randint(1, 120):03d}"  # Class of 120 students
                        if student_id not in voted_students:
                            voted_students.add(student_id)
                            break
                        attempts += 1
                    
                    if attempts >= 120:
                        # Ran out of unique students (unlikely unless requesting >120 votes)
                        break
                    
                    vote_time = question_time + timedelta(minutes=random.randint(1, 40))
                    votes.append({
                        "student_id": student_id,
                        "created_at": vote_time.isoformat()
                    })
                
                all_questions.append({
                    "question_id": f"q{question_global_id}",
                    "meeting_id": meeting["meeting_id"],
                    "question_number": q_num,
                    "student_id": f"student_{random.randint(1, 120):03d}",
                    "text": question_text,
                    "status": "posted",
                    "is_answered_in_class": random.random() < 0.3,  # 30% answered
                    "created_at": question_time.isoformat(),
                    "votes": votes
                })
                
                question_global_id += 1
        
        output = {"questions": all_questions}
        
        filepath = self.output_dir / "questions.json"
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"✓ Generated questions.json with {len(all_questions)} questions")
        return all_questions
    
    def generate_config_json(self):
        """Generate config.json file with system configuration."""
        config = {
            "config": [
                {
                    "key": "profanity_filter_enabled",
                    "value": "true",
                    "value_type": "boolean",
                    "description": "Enable profanity filtering for questions"
                },
                {
                    "key": "instructor_registration_enabled",
                    "value": "true",
                    "value_type": "boolean",
                    "description": "Allow new instructor registration"
                }
            ]
        }
        
        filepath = self.output_dir / "config.json"
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Generated config.json")
    
    def generate_all(self):
        """Generate all JSON files for the context."""
        print("="*70)
        print(f"🎯 Generating Demo Context: {self.context_name}")
        print(f"📖 Course: {self.context['title']}")
        print(f"📍 Output: {self.output_dir}")
        print("="*70)
        
        instructors = self.generate_instructors_json()
        classes = self.generate_classes_json(instructors)
        meetings = self.generate_meetings_json(instructors, classes)
        questions = self.generate_questions_json(meetings)
        self.generate_config_json()
        
        print("\n" + "="*70)
        print("✅ Context generation complete!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"  Instructors: {len(instructors)}")
        print(f"  Classes: {len(classes)}")
        print(f"  Meetings: {len(meetings)}")
        print(f"  Questions: {len(questions)}")
        print(f"  Total Votes: {sum(len(q['votes']) for q in questions)}")
        print("\n" + "="*70)
        print(f"\n🚀 To load this context:")
        print(f"  python demo/load_demo_context.py {self.context_name}")
        print(f"\n🐳 Or with Docker:")
        print(f"  DEMO_CONTEXT={self.context_name} docker-compose up")
        print("="*70 + "\n")


# Import APIKey for key generation
class APIKey:
    @staticmethod
    def generate_key():
        """Generate a secure API key."""
        import secrets
        return f"rmh_{secrets.token_urlsafe(32)}"


def main():
    parser = argparse.ArgumentParser(
        description="Generate realistic demo context for STEM courses"
    )
    parser.add_argument(
        "--context",
        required=True,
        choices=list(DemoContextGenerator.CONTEXTS.keys()),
        help="Context to generate"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: demo/data/{context})"
    )
    
    args = parser.parse_args()
    
    # Default output directory
    if args.output_dir is None:
        base_dir = Path(__file__).parent / "data" / args.context
    else:
        base_dir = args.output_dir
    
    generator = DemoContextGenerator(args.context, base_dir)
    generator.generate_all()


if __name__ == "__main__":
    main()
