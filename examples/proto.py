import sys

from nicegui import ui
from nicegui.elements.mixins.value_element import ValueElement
from pydantic import BaseModel


class Foo(BaseModel):
    id: str
    name: str


def fill_from_form(
    schema: type[BaseModel], form_elements: dict[str, ValueElement]
) -> BaseModel:
    data = {}
    for field in schema.model_fields.keys():
        if field in form_elements:
            data[field] = form_elements[field].value
    return schema.model_validate(data)


def formhandler(form_elements: dict[str, ValueElement], schema: type[BaseModel]):
    def clickhandler():
        record = fill_from_form(schema, form_elements)
        print(record)

    return clickhandler


@ui.page("/")
@ui.page("/{_:path}")
def index_page():
    form_elements = {}
    ui.label("Main Page")
    form_elements["name"] = ui.input("Name", value="John Doe")
    ui.button(
        "Click Me",
        on_click=formhandler(form_elements, Foo),
    )


def main(argv=sys.argv[1:]):
    ui.run(dark=True)


if __name__ in ("__main__", "__mp_main__"):
    main()
