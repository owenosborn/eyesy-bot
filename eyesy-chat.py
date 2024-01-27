import json
from io import StringIO
import os

import panel as pn
from openai import AsyncOpenAI

pn.extension()

system_message = f"""
You are a programming assistant helping to make python graphics programs using the PyGame library.  Specifically we are making small programs (called “modes”) for the Critter & Guitari Eyesy video synthesizer, so the python programs need to be in a certain format. They have a setup function and a draw function.  For example if the user says:

    draw a red circle at position 10,10 that is 10 pixels in diameter

You say:

    import pygame

    def setup(screen, etc):
        pass

    def draw(screen, etc):
        pygame.draw.circle(screen,(255,0,0),(10,10),(10))

setup() gets called once at the start and can be used to initialize things. draw() gets called every frame. Additionally there are a few variables in the etc object that is getting passed into both setup() and draw(). There are the variables etc.knob1, etc.knob2, etc.knob3, etc.knob4, and etc.knob5. These are all floating point numbers from 0-1 and can be used to control aspects of the graphics per the user request.  

Format output for markdown. Describe the code briefly in a sentance or two.
"""
first_message = "I am EYESY Bot! Type what you want to draw and I'll do my best to code it up!"
context = [ {'role':'system', 'content': f"""{system_message}"""} ] 

async def callback(contents: str, user: str, instance: pn.chat.ChatInterface):
    global context
    context.append({"role": "user", "content": contents})
    response = await aclient.chat.completions.create(
        #model="gpt-3.5-turbo",
        model="gpt-4",
        messages = context,
        stream=True,
    )
    message = ""
    async for chunk in response:
        part = chunk.choices[0].delta.content
        if part is not None:
            message += part
            yield message

    context.append({"role": "assistant", "content": message})
    print(context)
    print("response done")

def clear_chat(event):
    global context
    chat_interface.clear()
    context.clear()
    context = [ {'role':'system', 'content': f"""{system_message}"""} ] 
    chat_interface.send(first_message, user="EYESY Bot", respond=False)

# save button callback 
def generate_json():
    sio = StringIO()
    json.dump(context, sio, indent=4)
    sio.seek(0)
    return sio

# upload button callback
def process_upload(event):
    global context

    # Clear current context and chat
    chat_interface.clear()
    context.clear()
    chat_interface.send(first_message, user="EYESY Bot", respond=False)

    # Read uploaded JSON content
    if upload_button.value is not None:
        uploaded_content = upload_button.value.decode('utf-8')
        uploaded_context = json.loads(uploaded_content)

        # Reconstruct context and panels from uploaded data
        for message in uploaded_context:
            role = message['role']
            content = message['content']
            context.append({'role': role, 'content': content})

            if role == 'user':
                chat_interface.send(content, user="User", respond=False)

            elif role == 'assistant': 
                chat_interface.send(content, user="EYESY Bot", respond=False)
    else:
        print("No file uploaded")

aclient = AsyncOpenAI()
chat_interface = pn.chat.ChatInterface(
    callback=callback, 
    callback_user="EYESY Bot", 
    widgets=pn.widgets.TextAreaInput(
        placeholder="Enter message", 
        auto_grow=True, 
        max_rows=3
    ),
    message_params = dict(
        default_avatars={"System": "S", "User": "🦄", "EYESY Bot": "🤖"}, reaction_icons={"like": "thumb-up"},
        show_user=True,
        show_copy_icon=True,
        show_timestamp=True,
        show_reaction_icons=False,
        show_avatar=True
    ),
    show_undo=False,
    show_clear=False,
    show_rerun=False
)

chat_interface.send(first_message, user="EYESY Bot", respond=False)

clear_button = pn.widgets.Button(name='Clear', button_type='danger')

stylesheet = """
.bottom-button-row {
    margin-bottom: 10px; 
    margin-left: 5px; 
}
"""
db_stylesheet = """
:host(.bk-panel-models-widgets-FileDownload) .bk-btn {
    padding: 2px;
}
"""

download_button = pn.widgets.FileDownload(
    callback=generate_json, 
    label="Download Context", 
    filename="chat.json", 
    stylesheets=[db_stylesheet]
)

upload_button = pn.widgets.FileInput(accept='.json')
process_button = pn.widgets.Button(name='Upload Context')

clear_button.on_click(clear_chat)
process_button.on_click(process_upload)

button_row = pn.Row(
    download_button, 
    upload_button, 
    process_button, 
    clear_button,
    css_classes=['bottom-button-row']
)

pn.config.raw_css.append(stylesheet)

dashboard = pn.Column(chat_interface, button_row)

dashboard.servable()

