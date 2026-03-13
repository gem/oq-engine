# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# 
# Copyright (C) 2025, GEM Foundation
# 
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Support for onnxruntime sessions
"""
try:
    import onnxruntime
except ImportError:
    onnxruntime = None


# NB: the engine is already parallelizing, so we must disable the
# parallelization internal to onnxruntime to avoid oversubscription;
# it is the same reason why in baselib/__init__.py we have a line
# os.environ['OPENBLAS_NUM_THREADS'] = '1'
def get_session(model):
    """
    :param model: path to a machine learning model
    :returns: an InferenceSession with threads disabled suitable for the engine
    """
    opt = onnxruntime.SessionOptions()
    opt.inter_op_num_threads = 1
    opt.intra_op_num_threads = 1
    return onnxruntime.InferenceSession(
        model, opt, providers=onnxruntime.get_available_providers())


class PicklableInferenceSession:
    def __init__(self, model):
        self.model = model
        self.inference_session = get_session(self.model)

    def get_inputs(self):
        return self.inference_session.get_inputs()

    def run(self, *args):
        return self.inference_session.run(*args)

    def __getstate__(self):
        return {"model": self.model}

    def __setstate__(self, values):
        self.model = values["model"]
        self.inference_session = get_session(self.model)
