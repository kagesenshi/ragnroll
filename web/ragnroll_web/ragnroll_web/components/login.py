import reflex as rx
from ragnroll_web.state import State

def login():
    return rx.vstack(
        rx.span("Welcome!"),
        rx.span("Sign in or sign up to get started."),
        rx.box(),
        rx.box(
            rx.input(placeholder="Username", on_blur=State.set_username, mb=4),
            # rx.input(placeholder="Username", mb=4),
            rx.input(
                type_="password",
                placeholder="Password",
                on_blur=State.set_password,
                mb=4,
            ),
            rx.button(
                "Log in",
                on_click=State.login,
                bg="blue.500",
                color="white",
                _hover={"bg": "blue.600"},
            ),
            align_items="center",
            bg="white",
            border="1px solid #eaeaea",
            p=4,
            max_width="400px",
            border_radius="lg",
        ),
        
        rx.text(
            "Don't have an account yet?",
            rx.link("Sign up here.", href="/signup",color="blue.500"),
            color="gray.600",
        ),
        align='center',
        justify='center',
        style={'width': '100%', 'height': '100vh'}    
    )
    

