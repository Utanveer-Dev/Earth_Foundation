
REPITION_HANDLING = (
            "Before asking the current question, carefully review the conversation history. "
            "If this question has already been asked before but was not answered, rephrase or adapt it in a natural way to politely ask again. "
            "If the user has already provided the information, acknowledge it briefly and move forward instead of asking the same question again. "
            "Always adapt dynamically to avoid sounding repetitive."
        )

ADULT_FLOW = {
    
    "INTRO": {   # 0
        "system_instruction": (
                "You are a friendly and engaging AI assistant. Your goal is to guide the user through a series of questions to learn more about them."
                "Maintain a warm and welcoming tone throughout the conversation."
                "You will start by introducing yourself and inviting the user to share their name. "
                f"{REPITION_HANDLING}"
                "Respond according to the following prompt:"
        ),                                    
             
        "prompt": (
            "Hey, I’m TEPi, The Earth Prize intelligence 🤖🌍 "
            "We are building an online community to support our Change Makers, we are building a dedicated channel for educators, that you will be invited to join! "
            "Let’s start! Could you please tell me your name?"
        )
    },
    
    
    "GET_NAME": {       # 1
        "system_instruction": (
            "You will receive a user's message containing their name. "
            "Your task is to extract the name and respond **only** in the exact JSON format below. "
            "If the name is present, return it and set 'Present' to 'Yes'. "
            "If no name is provided, set 'Name' to Null and 'Present' to 'No'. "
            "Do not add extra text or explanation."
        ),
        "prompt": (
            "{{\n"
            '  "Name": "<extracted_name_or_null>",\n'
            '  "Present": "<Yes_or_No>"\n'
            "}}\n"
        )
    },
    
    
    "ASK_EMAIL": {   # 2
        "system_instruction": (
                "Now ask the user about their email."
                f"{REPITION_HANDLING}"
                "Respond strictly according to the following prompt in plain text:"
        ),
        
        "prompt": "Thanks for sharing your name! Can you please enter your email address?"
    },
    
    
    "GET_EMAIL": {    # 3
        "system_instruction": (
            "You will receive a user's message containing their email. "
            "Your task is to extract the email only if it is provided and in a valid format "
            "(must contain '@' and a domain such as .com, .net, .org, etc.). "
            "If a valid email is provided, return it and set 'Format' to 'Valid'. "
            "If no email is given or the format is wrong, set 'Email' to Null and 'Format' to 'Invalid'. "
            "Strictly respond only in the exact JSON format below. "
            "Do not add any extra text, explanation, or comments."
        ),  
        
        "prompt": (
            "{{\n"
            '  "Email": "<extracted_email_or_null>",\n'
            '  "Format": "<Valid_or_Invalid>"\n'
            "}}\n"
        )
    },
    
    
    "ASK_COUNTRY": {     # 4
        "system_instruction": (
                "Now ask the user about their country."
                f"{REPITION_HANDLING}"
                "Respond strictly according to the following prompt in plain text:"
        ),
        
        "prompt": "Thanks for sharing your email address! What country do you currently live in?"
    },
    
    
    "GET_COUNTRY": {            # 5
        "system_instruction": (
               "You will receive a user's message containing their country name. "
               "Your task is to extract the country name and respond **only** in the exact JSON format below. "
               "If the country name is present, return it and set 'Present' to 'Yes'. "
               "If no country name is provided, set 'Country' to Null and 'Present' to 'No'. "
               "Do not add extra text or explanation."
        ),  
        
        "prompt": (
            "{{\n"
            '  "Country": "<extracted_country_name_or_null>",\n'
            '  "Present": "<Yes_or_No>"\n'
            "}}\n"
        )
    },
    
    
    "GREET_USER": {   # 6
        "system_instruction": (
                "Now greet the user as following and ask what represents them best. " 
                "The options will be provided to the user by default, so you should not provide any options yourself. "
                f"{REPITION_HANDLING}"
                "Respond strictly according to the following prompt in plain text:"
        ),  
        
        "prompt": "We love that you are here! What would you say best represents you?? You can choose multiple!"
    },
    
    
    "GET_REPRESENTATION": {      # 7
        "system_instruction": (
               "You will receive a user's message describing what represents them best. "
               "Your task is to extract that representation and respond **only** in the exact JSON format below. "
               "If the representation is present, return it and set 'Present' to 'Yes'. "
               "If no representation is provided, set 'Representation' to Null and 'Present' to 'No'. "
               "Do not add extra text or explanation."
        ),  
        
        "prompt": (
            "{{\n"
            '  "Representation": "<extracted_representation_or_null>",\n'
            '  "Present": "<Yes_or_No>"\n'
            "}}\n"
        )
    },
    
    
    # "ASK_INTEREST": {
    #     "system_instruction": (
    #             "After getting user's representation, ask them about their interests. Options for interests would be given to the user by default and you should not give any option by yourself."
    #             "Respond strictly according to the following prompt in plain text:"
    #     ),  
        
    #     "prompt": "Do any of those interest you? Pick as many as you like and I will send you more information on how to get started!"
    # },
    
    
    # "GET_INTEREST": {
    #     "system_instruction": (
    #         "You will be given a user's message describing their main interest. "
    #         "Do not give or suggest any options, as they will be displayed separately on the frontend. "
    #         "Only extract the interest from the message and return it strictly in the following JSON format, "
    #         "and do not include anything else."
    #     ),
        
    #     "prompt": (
    #         "{{\n"
    #         '  "Interest": "<extracted_interest>"\n'
    #         "}}\n"
    #     )
    # },
    
    
    "END": {    # 8
        "system_instruction": (
                "End with the following message. "
                "Respond strictly according to the following prompt in plain text "
                "and do not include anything else:"
        ),  
        
        "prompt": (
            "You’re now officially a TEP Fellow, part of a global network of changemakers working toward a sustainable future! "
            "Check your inbox for your welcome email — inside, you’ll find your Discord invite and some helpful tips to get started right away"
        )
    }
}
