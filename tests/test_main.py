from unittest.mock import Mock, patch

from x2webhook import __main__


@patch("x2webhook.__main__.App")
@patch("x2webhook.__main__.get_config")
@patch("x2webhook.__main__.setup_logger")
def test_main(
    mock_setup_logger: Mock,
    mock_get_config: Mock,
    mock_app: Mock,
) -> None:
    # Arrange
    mock_get_config.return_value = Mock()
    mock_app.return_value = Mock()

    # Act
    __main__.main()

    # Assert
    mock_get_config.assert_called()
    mock_setup_logger.assert_called()
