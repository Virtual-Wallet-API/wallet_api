from app.schemas.card import CardPublicResponse, CardResponse
from app.schemas.contact import ContactPublicResponse, ContactResponse
from app.schemas.user import UserResponse, UserPublicResponse

# Rebuild models after all schemas are defined
UserResponse.model_rebuild()
UserPublicResponse.model_rebuild()
ContactPublicResponse.model_rebuild()
ContactResponse.model_rebuild()
CardPublicResponse.model_rebuild()
CardResponse.model_rebuild()
