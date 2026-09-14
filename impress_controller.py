import os
import time
import subprocess
import uno

# ==========================
# LibreOffice UNO Settings
# ==========================

UNO_HOST = "localhost"
UNO_PORT = "2002"


# ==========================
# Connect to LibreOffice
# ==========================

def connect():

    # Create local UNO context
    local_context = uno.getComponentContext()

    # Create URL resolver
    resolver = local_context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver",
        local_context,
    )

    uno_url = (
        f"uno:socket,host={UNO_HOST},port={UNO_PORT};"
        "urp;StarOffice.ComponentContext"
    )

    # ----------------------------------------
    # Try connecting to an already running
    # LibreOffice instance
    # ----------------------------------------
    try:
        return resolver.resolve(uno_url)

    except Exception:
        pass

    # ----------------------------------------
    # If not running, launch LibreOffice
    # ----------------------------------------
    subprocess.Popen([
        "soffice",
        "--impress",
        "--norestore",
        f"--accept=socket,host={UNO_HOST},port={UNO_PORT};urp;",
    ])

    # Wait up to 30 seconds
    timeout = time.time() + 30

    while time.time() < timeout:
        try:
            return resolver.resolve(uno_url)

        except Exception:
            time.sleep(1)

    raise TimeoutError("เชื่อมต่อ LibreOffice ไม่สำเร็จภายใน 30 วินาที")


# ==========================
# Get Desktop Object
# ==========================

def get_desktop(context):

    service_manager = context.ServiceManager

    desktop = service_manager.createInstanceWithContext(
        "com.sun.star.frame.Desktop",
        context,
    )

    return desktop


# ==========================
# Open Presentation
# and Go To Slide
# ==========================

def open_and_goto(desktop, file_path, slide_number):

    # Convert local path -> file URL
    absolute_path = os.path.abspath(file_path)
    file_url = uno.systemPathToFileUrl(absolute_path)

    document = None

    # ----------------------------------------
    # Check whether this presentation
    # is already opened
    # ----------------------------------------
    components = desktop.Components.createEnumeration()

    while components.hasMoreElements():

        component = components.nextElement()

        try:
            if (
                hasattr(component, "getPresentation")
                and component.getURL() == file_url
            ):
                document = component
                break

        except Exception:
            continue

    # ----------------------------------------
    # If not opened, open it
    # ----------------------------------------
    if document is None:
        document = desktop.loadComponentFromURL(
            file_url,
            "_blank",
            0,
            (),
        )

    presentation = document.getPresentation()

    # ----------------------------------------
    # Start slideshow if needed
    # ----------------------------------------
    if not presentation.isRunning():

        presentation.start()

        timeout = time.time() + 10

        while (
            not presentation.isRunning()
            and time.time() < timeout
        ):
            time.sleep(0.1)

        # Give LibreOffice a little time
        time.sleep(1)

    # ----------------------------------------
    # Jump to desired slide
    # ----------------------------------------
    controller = presentation.getController()
    controller.gotoSlideIndex(slide_number - 1)

    # LibreOffice quirk: the first gotoSlideIndex call sometimes updates the
    # slide position internally but doesn't redraw the screen until another
    # goto command comes in. Call it again immediately so one click is enough.
    controller.gotoSlideIndex(slide_number - 1)

    return document
