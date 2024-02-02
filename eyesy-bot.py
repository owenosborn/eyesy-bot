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

setup() gets called once at the start and can be used to initialize things. draw() gets called every frame. Additionally there are a few variables in the etc object that is getting passed into both setup() and draw(). The `etc` object contains the following:

--- begin eyesy api

-   `etc.audio_in` - A *list* of the 100 most recent audio levels registered by EYESY's audio input. The 100 audio values are stored as 16-bit, signed integers, ranging from a minimum of -32,768 to a maximum of +32,767.
-   `etc.audio_trig` - A *boolean* value indicating a trigger event.    
-	 `etc.xres` - A *float* of the horizontal component of the current output resolution. 
-	 `etc.yres` - A *float* of the vertical component of the current output resolution. 
-   `etc.knob1` - A *float* representing the current value of *Knob 1*. 
-   `etc.knob2` - A *float* representing the current value of *Knob 3*. 
-   `etc.knob3` - A *float* representing the current value of *Knob 3*. 
-   `etc.knob4` - A *float* representing the current value of *Knob 4*. 
-   `etc.knob5` - A *float* representing the current value of *Knob 5*. 
-   `etc.lastgrab` - A **Pygame** *surface* that contains an image of the last taken screenshot taken (via the *Screenshot* button). This surface has dimensions of 1280 by 720, matching the full size of the screenshot.
-   `etc.lastgrab_thumb` - A **Pygame** *surface* that contains a thumbnail image of the last taken screenshot taken (via the *Screenshot* button). This surface has dimensions of 128 by 72.
-   `etc.midi_notes` - A *list* representing the 128 various MIDI note pitches. Each value in this list indicates whether that note is current on or not. For example, you could create a function that executes when “middle C” (MIDI note 60) is on with something like…

    if etc.midi_notes[60] : yourFunctionHere()

-   `etc.midi_note_new` - A *boolean* value indicating whether or not at least one new MIDI note on message was received since the last frame was drawn (via the `draw()`function).

-   `etc.mode` - A *string* of the current mode’s name.
-   `etc.mode_root` - A *string* of the file path to the current mode’s folder. This will return something like `/sdcard/Modes/Python/CurrentModeFolder`. This can be useful when images, fonts, or other resources need to be loaded from the mode’s folder. (The `setup()` function would be an appropriate place to do this.)

--- end eyesy api

Format output for markdown. Output python code first then describe the code briefly in a sentance or two.
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
    padding: 8px;
}
"""

download_button = pn.widgets.FileDownload(
    callback=generate_json, 
    label="Download Chat", 
    filename="chat.json", 
    stylesheets=[db_stylesheet]
)

upload_button = pn.widgets.FileInput(accept='.json')
process_button = pn.widgets.Button(name='Upload Chat')

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

dashboard.servable(title="EYESY Bot")

