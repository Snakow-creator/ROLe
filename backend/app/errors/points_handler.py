# from fastapi import Request, APIRouter
# from fastapi.responses import JSONResponse

# from errors.points import NotEnoughSpointsError
# from web_notices import error_item_notice

# router = APIRouter(tags=['errors'])

# async def not_enough_spoints_handler(request: Request, exc: NotEnoughSpointsError):
#     print("HANDLERHANDLERHANDLERHANDLER")
#     return JSONResponse(
#         status_code=402,
#         content={
#             "error": "not_enough_spoints",
#             "message": str(exc),
#             "notice": error_item_notice(),
#         },
#     )

# handlers = [
#     (NotEnoughSpointsError, not_enough_spoints_handler),
# ]
