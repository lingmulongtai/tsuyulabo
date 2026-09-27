from __future__ import annotations

import pytest
import torch
from tsuyu_brain.api import predict_behavior
from tsuyu_brain.learning import new_fly_state
from tsuyu_brain.params import default_params


def test_game_decoder_rejects_unvalidated_connectome() -> None:
    threads = torch.get_num_threads()
    try:
        torch.set_num_threads(1)
        state = new_fly_state(default_params(), "malecns-v1.0")
        with pytest.raises(ValueError, match="no validated behavior decoder"):
            predict_behavior(state, "sugar")
    finally:
        torch.set_num_threads(threads)
