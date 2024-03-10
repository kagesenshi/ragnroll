import reflex as rx
from ragnroll_web.state import State

def login():
    return rx.chakra.vstack(
        rx.chakra.span("Welcome!"),
        rx.chakra.span("Sign in or sign up to get started."),
        rx.chakra.box(),
        rx.chakra.box(
            rx.chakra.input(placeholder="Username", on_blur=State.set_username, mb=4),
            # rx.chakra.input(placeholder="Username", mb=4),
            rx.chakra.input(
                type_="password",
                placeholder="Password",
                on_blur=State.set_password,
                mb=4,
            ),
            rx.chakra.button(
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
        
        rx.chakra.text(
            "Don't have an account yet?",
            rx.chakra.link("Sign up here.", href="/signup",color="blue.500"),
            color="gray.600",
        ),
        align='center',
        justify='center',
        style={'width': '100%', 'height': '100vh'}    
    )
    

