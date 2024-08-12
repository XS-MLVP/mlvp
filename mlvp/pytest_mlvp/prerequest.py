from ..reporter import set_func_coverage, set_line_coverage

class PreRequest:
    def __init__(self):
        self.dut = None
        self.args = None
        self.request_name = None
        self.cov_groups = []

        self.waveform_filename = None
        self.coverage_filename = None

    def __add_cov_sample(self, cov_groups):
        """
        Add the coverage sample to the DUT.
        """

        assert self.dut is not None, "The DUT has not been set."
        assert self.cov_groups is not None, "The coverage group has not been set."

        if not isinstance(cov_groups, list):
            cov_groups = [cov_groups]

        for g in cov_groups:
            self.dut.xclock.StepRis(
                lambda _: g.sample()
            )

    def create_dut(self, dut_cls, clock_name=None, waveform_filename=None, coverage_filename=None):
        """
        Create the DUT.

        Args:
            dut_cls: The DUT class.
            clock_name: The clock pin name.
            waveform_filename: The waveform filename. if not set, it will be set to default.
            coverage_filename: The coverage filename. if not set, it will be set to default.

        Returns:
            The DUT instance.
        """

        self.waveform_filename = f"report/{dut_cls.__name__}_{self.request_name}.fst"
        self.coverage_filename = f"report/{dut_cls.__name__}_{self.request_name}.dat"

        if waveform_filename is not None:
            self.waveform_filename = waveform_filename
        if coverage_filename is not None:
            self.coverage_filename = coverage_filename

        self.dut = dut_cls(
            waveform_filename=self.waveform_filename,
            coverage_filename=self.coverage_filename
        )

        if clock_name:
            self.dut.InitClock(clock_name)

        if self.cov_groups is not None:
            self.__add_cov_sample(self.cov_groups)

        return self.dut

    def add_cov_groups(self, cov_groups, periodic_sample=True):
        """
        Add the coverage groups to the list.

        Args:
            cov_groups: The coverage groups to be added.
            periodic_sample: Whether to sample the coverage periodically.
        """

        if not isinstance(cov_groups, list):
            cov_groups = [cov_groups]
        self.cov_groups.extend(cov_groups)

        if self.dut is not None:
            self.__add_cov_sample(cov_groups)

    def finish(self, request):
        """
        Finish the request.
        """

        if self.dut is not None:
            self.dut.Finish()
            set_func_coverage(request, self.cov_groups)
            set_line_coverage(request, self.coverage_filename)

        for g in self.cov_groups:
            g.clear()

        self.cov_groups.clear()
