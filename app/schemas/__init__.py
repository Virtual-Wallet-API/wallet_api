from app.schemas.card import CardPublicResponse, CardPrivateResponse
from app.schemas.user import UserResponse, UserPublicResponse
from app.schemas.contact import ContactPublicResponse, ContactResponse

# Rebuild models after all schemas are defined
UserResponse.model_rebuild()
UserPublicResponse.model_rebuild()
ContactPublicResponse.model_rebuild()
ContactResponse.model_rebuild()
CardPublicResponse.model_rebuild()
CardPrivateResponse.model_rebuild()