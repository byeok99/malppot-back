from fastapi import HTTPException, status


class ErrorCode:
    # Auth
    MISSING_AUTH_CODE = "Missing authorization code."
    FAILED_GET_ACCESS_TOKEN_GOOGLE = "Failed to get access token from Google."
    FAILED_GET_USER_INFO_GOOGLE = "Failed to get user info from Google."
    REJECT_REGISTER_USER = "서비스가 운영중이지 않습니다."
    INVALID_OR_EXPIRED_TOKEN = "Invalid or expired token."
    AUTHENTICATION_TOKEN_MISSING = "Authentication token missing."
    INVALID_CREDENTIALS = "Invalid credentials."
    USER_NOT_FOUND = "User not found."

    # Malbeot
    MALBEOT_CHAT_FAILED = "Failed to process chat request."
    MALBEOT_MODEL_ERROR = "Malbeot model returned an error."

    # Speech
    SPEECH_EVALUATION_FAILED = "Speech evaluation failed."
    SPEECH_AUDIO_PROCESSING_ERROR = "Audio processing error."

    # Heygen
    HEYGEN_VIDEO_CREATION_FAILED = "Failed to create Heygen video."
    HEYGEN_VIDEO_STATUS_CHECK_FAILED = "Failed to check Heygen video status."
    HEYGEN_API_ERROR = "Heygen API error."
    HEYGEN_VIDEO_NOT_READY = "Heygen video is not yet ready."
    HEYGEN_REQUEST_FAILED = "Heygen request failed."  # 일반적인 Heygen API 요청 실패

    # MyPage
    MYPAGE_DATA_NOT_FOUND = "My page data not found."
    MYPAGE_UPDATE_FAILED = "Failed to update my page data."


class CustomException(HTTPException):
    def __init__(self, status_code: int, detail: str, **kwargs):
        super().__init__(status_code=status_code, detail=detail, **kwargs)


# Auth
class MissingAuthCodeException(CustomException):
    def __init__(self, detail: str = ErrorCode.MISSING_AUTH_CODE):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class FailedGoogleAccessTokenException(CustomException):
    def __init__(self, detail: str = ErrorCode.FAILED_GET_ACCESS_TOKEN_GOOGLE):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class FailedGoogleUserInfoException(CustomException):
    def __init__(self, detail: str = ErrorCode.FAILED_GET_USER_INFO_GOOGLE):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class rejectRegisterUser(CustomException):
    def __init(self, detail: str = ErrorCode.REJECT_REGISTER_USER):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class InvalidTokenException(CustomException):
    def __init__(self, detail: str = ErrorCode.INVALID_OR_EXPIRED_TOKEN):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthenticationTokenMissingException(CustomException):
    def __init__(self, detail: str = ErrorCode.AUTHENTICATION_TOKEN_MISSING):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class InvalidCredentialsException(CustomException):
    def __init__(self, detail: str = ErrorCode.INVALID_CREDENTIALS):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class UserNotFoundException(CustomException):
    def __init__(self, detail: str = ErrorCode.USER_NOT_FOUND):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


# Malbeot 관련 커스텀 예외
class MalbeotChatException(CustomException):
    def __init__(self, detail: str = ErrorCode.MALBEOT_CHAT_FAILED):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class MalbeotModelException(CustomException):
    def __init__(self, detail: str = ErrorCode.MALBEOT_MODEL_ERROR):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


# Speech 관련 커스텀 예외
class SpeechEvaluationException(CustomException):
    def __init__(self, detail: str = ErrorCode.SPEECH_EVALUATION_FAILED):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class SpeechAudioProcessingException(CustomException):
    def __init__(self, detail: str = ErrorCode.SPEECH_AUDIO_PROCESSING_ERROR):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


# Heygen 관련 커스텀 예외
class HeygenVideoCreationException(CustomException):
    def __init__(self, detail: str = ErrorCode.HEYGEN_VIDEO_CREATION_FAILED):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class HeygenVideoStatusException(CustomException):
    def __init__(self, detail: str = ErrorCode.HEYGEN_VIDEO_STATUS_CHECK_FAILED):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class HeygenApiException(CustomException):
    def __init__(self, detail: str = ErrorCode.HEYGEN_API_ERROR,
                 status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)


class HeygenVideoNotReadyException(CustomException):
    def __init__(self, detail: str = ErrorCode.HEYGEN_VIDEO_NOT_READY):
        super().__init__(status_code=status.HTTP_202_ACCEPTED, detail=detail)  # 202 Accepted는 진행 중임을 의미


class HeygenRequestException(CustomException):
    def __init__(self, detail: str = ErrorCode.HEYGEN_REQUEST_FAILED, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


# MyPage 관련 커스텀 예외
class MyPageDataNotFoundException(CustomException):
    def __init__(self, detail: str = ErrorCode.MYPAGE_DATA_NOT_FOUND):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class MyPageUpdateException(CustomException):
    def __init__(self, detail: str = ErrorCode.MYPAGE_UPDATE_FAILED):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
