class Display:
    def __init__(selfoverall_progress):
        pass

    def progress_start(self):
        self.overall_progress = {}
        self.process_progress = {}
        self.metadata = {}

    def progress_stop(self):
        pass

    def progress_update(
        self, overall_progress=None, process_progress=None, metadata=None
    ):
        if overall_progress:
            self.overall_progress |= overall_progress
        if process_progress:
            self.process_progress |= process_progress
        if metadata:
            self.metadata_progress |= metadata_progress
