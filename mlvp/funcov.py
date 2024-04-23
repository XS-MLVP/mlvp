from typing import Union, Callable
from collections import OrderedDict
import inspect
import json
from .base import MObject


class CovCondition(MObject): 
    """
    CovCondition class
    """
    def __check__(self, target) -> bool:
        raise NotImplementedError("Method __check__ is not implemented")        
    def __call__(self, target) -> bool:
        return self.__check__(target.value)

class CovEq(CovCondition):
        """
        CovEq class, check if the target is equal to the value
        """
        def __init__(self, value) -> None:
            self.value = value        
        def __check__(self, target) -> bool:
            return target == self.value

class CovGt(CovCondition):
        """
        CovGt class, check if the target is greater than the value
        """
        def __init__(self, value) -> None:
            self.value = value        
        def __check__(self, target) -> bool:
            return target > self.value

class CovLt(CovCondition):
        """
        CovLt class, check if the target is less than the value
        """
        def __init__(self, value) -> None:
            self.value = value        
        def __check__(self, target) -> bool:
            return target < self.value

class CovGe(CovCondition):
        """
        CovGe class, check if the target is greater or equal to the value
        """
        def __init__(self, value) -> None:
            self.value = value        
        def __check__(self, target) -> bool:
            return target >= self.value

class CovLe(CovCondition):
        """
        CovLe class, check if the target is less or equal to the value
        """
        def __init__(self, value) -> None:
            self.value = value        
        def __check__(self, target) -> bool:
            return target <= self.value

class CovNe(CovCondition):
        """
        CovNe class, check if the target is not equal to the value
        """
        def __init__(self, value) -> None:
            self.value = value        
        def __check__(self, target) -> bool:
            return target != self.value

class CovIn(CovCondition):
        """
        CovIn class, check if the target is in the value
        """
        def __init__(self, value) -> None:
            self.value = value        
        def __check__(self, target) -> bool:
            return target in self.value

class CovNotIn(CovCondition):
        """
        CovNotIn class, check if the target is not in the value
        """
        def __init__(self, value) -> None:
            self.value = value        
        def __check__(self, target) -> bool:
            return target not in self.value

class CovIsInRange(CovCondition):
        """
        CovIsInRange class, check if the target is in the range
        """
        def __init__(self, low, high) -> None:
            self.low = low
            self.high = high
        def __check__(self, target) -> bool:
            return self.low <= target <= self.high

# aliases
Eq = CovEq
Gt = CovGt
Lt = CovLt
Ge = CovGe
Le = CovLe
Ne = CovNe
In = CovIn
NotIn = CovNotIn
IsInRange = CovIsInRange


class CovGroup(object):
    """
    functional coverage group
    """

    def __init__(self, name: str = "", disable_sample_when_hinted=True) -> None:
        """
        CovGroup constructor
        @param name: name of the group
        @param disable_sample_when_hinted: if True, the group will stop sampling when all points are hinted
        """
        frame = inspect.stack()[1]
        self.filename = frame.filename
        self.lineno = frame.lineno
        self.name = name if name else "%s:%s" % (self.filename, self.lineno)
        self.cov_points = OrderedDict()
        self.disable_sample_when_hinted = disable_sample_when_hinted
        self.hinted = False
        self.stop_sample = False
        self.sample_count = 0
        self.sample_calln = 0
    
    def add_watch_point(self, target: object, bins: Union[dict, CovCondition, Callable[[object, object], bool]], check_func: dict = {}, name: str = ""):
        """
        Add a watch point to the group
        @param target: the object to be watched, need to have a value attribute. eg target.value is available
        @param bins: a dict of CovCondition objects, a single CovCondition object or a Callable object (its params is call(target) -> bool).
        @param check_func: a dict of functions to check the condition, the key should be the same as bins, the value shoud be a function. \
            the function should have the signature of func(target, covcondtion, points) -> bool. Arg target is the original data to check. Arg \
            covcondtion is the condition data in bins. Arg points is the points in CovGroup object. If the function is not provided, \
            the default check function will be used.
        @param name: the name of the point
        """
        key  = name
        if not key:
            key = "%s:%s" % (target, bins.keys())
        if key in self.cov_points:
            raise ValueError("Duplicated key %s" % key)
        if not isinstance(bins, dict):
            if not callable(bins):
                raise ValueError("Invalid value %s for key %s" % (bins, key))
            bins = {"anonymous": bins}
        for k, v in bins.items():
            if not callable(v):
                raise ValueError("Invalid value %s for key %s" % (v, k))        
        self.cov_points[key] = {"taget": target, "bins": bins, "check_func": check_func, "hints": {k: 0 for k in bins.keys()}, "hinted": False}

    @staticmethod    
    def __check__(points) -> bool:
        hinted = True
        for k, b in points["bins"].items():
            check_func = points["check_func"].get(k)
            hints = points["hints"][k]

            if check_func:
                hints += 1 if check_func(points["taget"], b, points) else 0
            else:
                hints += 1 if b(points["taget"]) else 0
            if hints == 0:
                hinted = False
            
            points["hints"][k] = hints
        points["hinted"] = hinted
        return hinted
    
    def cover_points(self):
         """
         return the name list for all points
         """
         return self.cov_points.keys()

    def cover_point(self, key: str):
        """
        return the point with key
        @param key: the key of the point
        """
        if key not in self.cov_points:
            raise ValueError("Invalid key %s" % key)
        return self.cov_points[key]

    def is_point_covered(self, key: str) -> bool:
        """
        check if the point with key is covered
        @param key: the key of the point
        """
        if key not in self.cov_points:
            raise ValueError("Invalid key %s" % key)
        return self.cov_points[key]["hinted"]
    
    def is_all_covered(self) -> bool:
        """
        check if all points are covered
        """
        if self.hinted:
            return True
        for _, v in self.cov_points.items():
            if not v["hinted"]:
                return False
        return True

    def sample(self):
        """
        sample the group
        """
        self.sample_calln += 1
        if self.stop_sample:
            return
        if self.hinted and self.disable_sample_when_hinted:
            return
        self.sample_count += 1
        all_hinted = True
        for _, v in self.cov_points.items():
            if not self.__check__(v):
                all_hinted = False
        self.hinted = all_hinted
    
    def sample_stoped(self):
        """
        check if the group is stoped
        """
        if self.stop_sample:
            return True
        return self.hinted and self.disable_sample_when_hinted
    
    def stop_sample(self):
        """
        stop sampling
        """
        self.stop_sample = True
    
    def resume_sample(self):
        """
        resume sampling
        """
        self.stop_sample = False

    def as_dict(self):
        """
        return the group as a dict
        """
        ret = OrderedDict()
        for k, v in self.cov_points.items():
            ret[k] = {"hinted": v["hinted"], "hints": v["hints"]}
        ret["__name__"] = self.name
        ret["__hinted__"] = self.hinted
        ret["__filename__"] = self.filename
        ret["__lineno__"] = self.lineno
        ret["__disable_sample_when_hinted__"] = self.disable_sample_when_hinted
        ret["__sample_count__"] = self.sample_count
        ret["__sample_calln__"] = self.sample_calln
        return ret

    def __str__(self) -> str:
        """
        return the group as a json string
        """
        return json.dumps(self.as_dict(), indent=4)

