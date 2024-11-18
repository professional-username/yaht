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
    # The full range of variables that the progress update should accept
    new_progress_update = {
        "lab_name": "FOOBAR",
        "process_count": 10,
    }

    # TODO: What exactly should be passed to progress_update()??

    disp = Display()
    disp.progress_start()
    disp.progress_update(**new_progress_update)
    disp.progress_end()


def test_progressive_progress_update():
    """Test that we can send a progress update for only a single variable"""
    disp = Display()
    disp.progress_start()
    disp.progress_update(lab_name="FOOBAR", lab_length=1)
    disp.progress_update(lab_progress=1, experiment_name="foo", experiment_length=3)
    disp.progress_update(experiment_progress=1, trial_name="bar", trial_length=2)
    disp.progress_update(trial_progress=1, process_name="foobar", process_length=2)
    disp.progress_update(process_progress=2)
