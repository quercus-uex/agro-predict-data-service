import threading


def _background_task(
    app,
    func,
    *args,
    **kwargs
):
    with app.app_context():
        func(*args, **kwargs)

def lanzar_ingesta_background(
    app,
    funcion,
    *args,
    **kwargs
):
    """
    Configuración de hilo en segundo plano que 
    almacena datos solicitados en la base de datos
    """
    thread = threading.Thread(
        target = _background_task,
        args = (
            app,
            funcion,
            *args
        ),
        kwargs = kwargs,
        daemon = True
    )
    thread.start()