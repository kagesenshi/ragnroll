from ..components.code_form import code_form
from ..components.util import main_template
import reflex as rx

EXPERTISE_SAMPLE='''

'''
@rx.page(route='/expertise')
def index() -> rx.Component:
    return main_template(code_form())