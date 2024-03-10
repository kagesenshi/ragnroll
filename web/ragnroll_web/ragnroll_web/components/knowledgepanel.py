import reflex as rx

from ragnroll_web.state import State

def panel_style():
    return {
        "bg": "white",
        "border_radius": "15px",
        "border_color": "lightgrey",
        "border_width": "thin",
        "padding": 5,
        "style": {"boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"},
        # "width": "340px",
        "width": "500px",
    }
    
    
def thing_template() -> rx.Component:
    styles = panel_style()
    return rx.chakra.box(
        rx.chakra.vstack(
            rx.chakra.heading('Title', size="md"),
            rx.chakra.image(
                src= "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRtdnR2i_9aipQLrEkLzm7NNxzy6mwhNjDYijEQMLgPMEwr6MsY7SiqXSuEDyTEjO9GKfU&usqp=CAU",
                width = "auto",
                height = "auto",
            ),
            align_items = "left",
            align="start"
        ),
        **panel_style(),
        display=["none", "none", "none", "flex", "flex", "flex"]
    )

def knowledgepanel() -> rx.Component:
    return thing_template()


#Use Cond() if you need it to update based on State variable value changes
# def knowledgepanel() -> rx.Component:
#     return rx.cond(
#         State.valid_input,
#         rx.cond(
#             State.kp_type == "person", person_template(),
#             rx.cond(
#                 State.kp_type == "place", place_template(),
#                 rx.cond(
#                     State.kp_type == "organization", organization_template(),
#                     rx.cond(
#                         State.kp_type == "thing", thing_template(),
#                         None # This is the default case when none of the conditions are met.
#                     )
#                 )
#             )
#         ),
#         rx.chakra.box() # If State.valid_input is False, an empty rx.chakra.box() is returned
#         # rx.chakra.box("width": "340px")
#     )
