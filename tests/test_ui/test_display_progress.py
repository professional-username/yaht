from yaht.display import Display


def test_progress_start_stop():
    """
    Test that after initializing the display
    we can start and stop the progress display
    """
    disp = Display()
    disp.progress_start()
    disp.progress_stop()


def test_progress_update():
    """Test that we can send a progress update to the display"""
    disp = Display()
    disp.progress_start()
    # Two empty types of progress updates should work here
    disp.progress_update(overall_progress={}, process_progress={}, metadata={})
    disp.progress_update()
    disp.progress_stop()


def test_progress_loop():
    """Test sending progress updated in a loop, as we might in practice"""
    disp = Display()
    disp.progress_start()

    # Run a loop and send some data each loop
    for i in range(10):
        disp.progress_update(
            overall_progress={
                "total": 10,
                "current": i,
            }
        )

    disp.progress_stop()
