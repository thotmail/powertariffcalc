import abc
from abc import ABC, abstractmethod

theRest = chr(153)


def promptInt(msg, caster=int, r=None):
    a = ''
    while a == '':
        try:
            a = caster(input(msg))
            if a not in r or a < 0:
                a = ''
        except ValueError:
            a = ''
        except TypeError:
            pass
    return a


def promptFromList(lst):
    if len(lst) == 1:
        f = 0
    else:
        print("Options:")

        for i in range(len(lst)):
            print(f"{i}: {lst[i]}")

        f = promptInt(f"Please Select(0-{len(lst)-1}):", int,
                      range(len(lst)))

    return f


class Cost(ABC):
    # 0 - in name (units, kw...)
    # 1 - type of in (int, float, choice)
    # 2 - aux to 1, (list of choices or range for int)
    @abc.abstractproperty
    def requiredIns():
        pass

    @abstractmethod
    def calcCost(self, ins):
        pass

    def __add__(self, b):
        return CostAdd(self, b)

    def __sub__(self, b):
        return CostSub(self, b)

    def __mul__(self, b):
        return CostMul(self, b)


# parent of opperation classes
class CostOP(Cost):
    def __init__(self, a, b):
        self._a = a
        self._b = b

    def requiredIns(self):
        return self._a.requiredIns() + self._b.requiredIns()

    def calcCost(self, ins):
        pass


class CostAdd(CostOP):
    def calcCost(self, ins):
        return self._a.calcCost(ins) + self._b.calcCost(ins)


class CostSub(CostOP):
    def calcCost(self, ins):
        return self._a.calcCost(ins) - self._b.calcCost(ins)


class CostMul(CostOP):
    def calcCost(self, ins):
        return self._a.calcCost(ins) * self._b.calcCost(ins)


# for cost format of:
# for the first 50 x, cost is 1 per x,
# for the next 100 x cost is 2 per x,
# and 3 per x for the rest
# translates to:
# CostPerUnit({50: 1, 100: 2, theRest: 3})
class CostPerUnit(Cost):

    def __init__(self, costbrackets, unitName="units"):
        """ Cost depends on quantity of single variable, cost format of:
            cost = v1 for the first k1 of x
            cost = v2 for the rest
            written as CostPerUnit({k1:v1, theRest:v2}, x)
        Args:
            costbrackets (dict): keys representing quantity, values represent cost
            unitName (str, optional): name of the variable that cost depends on. Defaults to "units".
        """
        self._brackets = costbrackets
        self._unitName = unitName

    def requiredIns(self):
        return([[self._unitName, 'float']])

    def calcCost(self, ins):
        cost = 0
        counter = ins[self._unitName]
        for i in self._brackets:
            if i == theRest or i >= counter:
                cost += self._brackets[i] * counter
                counter = 0
                break
            elif i == -1:
                raise ValueError(
                    f"""{self._unitName} exceds allowable max.\n
                    {ins[self._unitName]} > {list(self._brackets.keys())[-2]}
                    """)
            else:
                cost += self._brackets[i]*i
                counter -= i

        if counter != 0:
            raise ValueError(
                f"""{self._unitName} exceds allowable max.\n
                {ins[self._unitName]} > {list(self._brackets.keys())[-1]}""")

        return cost


# for cost format of:
# if you have a, cost is 1,
# if you have b, cost is 2,
# translates to:
# CostPerUnit([ [a, 1], [b, 2] ])
class CostPerChoice(Cost):
    def __init__(self, choices, unitName="choices"):
        """When Cost is based on distinct catagories

        Args:
            choices (list): list containing lists of length 2, 0: catagory, 1: cost associated with the catagory
            unitName (str, optional): name of the variable that cost depends on. Defaults to "choices".
        """
        self._choices = choices
        self._unitName = unitName

    def requiredIns(self):
        return([[self._unitName, 'choice', [i[0] for i in self._choices]]])

    def calcCost(self, ins):
        cost = self._choices[ins[self._unitName]][1]
        return cost


# for cost format of:
# cost is x
# translates to:
# CostFlat(x)
class CostFlat(Cost):
    def __init__(self, flat):
        """When theres is a cost that doesnt depend on variables

        Args:
            flat (int): the cost
        """
        self._f = flat

    def requiredIns(self):
        return([])

    def calcCost(self, ins):
        return self._f


# for cost format of:
# for the first 50 x, cost is 1 per x,
# for the next 100 x cost is 2 per x,
# 3 per x for the rest,
# an aditional 4 for every x above contract
# translates to:
# CostPerUnit({50: 1, 100: 2, theRest: 3, -1: 4})

# for cost format of:
# for x up to contract, cost is 1 per x,
# for x above contract, cost is 2 per x
# translates to:
# CostPerUnit({theRest: 1, -1: (2-1)})
class CostPerUnitContract(CostPerUnit):
    def __init__(self, costbrackets, contractName="contract demand kW",
                 unitName="kW"):
        """When theres a contract on what the max should be, see CostPerUnit
        key = -1 for cost above contract

        Args:
            costbrackets (dict): keys representing quantity, values represent cost
            contractName (str, optional): name of variable representing contract max amount. Defaults to "contract demand kW".
            unitName (str, optional): name of the variable that cost depends on. Defaults to "kW".
        """
        super().__init__(costbrackets, unitName)
        self._cName = contractName

    def requiredIns(self):
        return super().requiredIns()+[[self._cName, 'float']]

    def calcCost(self, ins):
        cost = super().calcCost(ins)
        if ins[self._unitName] > ins[self._cName]:
            cost += (ins[self._unitName] - ins[self._cName]) * \
                self._brackets[-1]

        return cost


# for cost format of:
# if y <= a, cost is 1 per x,
# if y > a, cost is 2 per x
# translates to:
# CostPerUnitConditional({a: 1, thRest: 2})
class CostPerUnitConditional(CostPerUnit):
    def __init__(self, costbrackets, conditionalName="kW", unitName="units"):
        """When cost per x depends on y:
        if x <= k1, cost is v1 per y
        if x <= k2, cost is v2 per y
        if x > k2, cost is v3 per y
        CostPerUnitConditional({k1: v1, k2: v2, thRest: v3}, x, y)
        Args:
            costbrackets (dict): keys representing quantity, values represent cost
            conditionalName (str, optional): the y that cost per x depends on. Defaults to "kW".
            unitName (str, optional): the x in cost pre x. Defaults to "units".
        """
        super().__init__(costbrackets, unitName)
        self._cName = conditionalName

    def requiredIns(self):
        return super().requiredIns()+[[self._cName, 'float']]

    def calcCost(self, ins):
        cost = 0
        counter = ins[self._cName]
        for i in self._brackets:
            if counter <= i or i == theRest:
                cost += self._brackets[i] * counter
                counter = 0
                break

        if counter != 0:
            raise ValueError(
                f"""{self._cName} exceds allowable max.\n{ins[self._cName]} >
                 {list(self._brackets.keys())[-1]}""")

        return cost


# bracket: 0 - cost of imp 90 to 95
#           1 - cost of imp above 95
#           2 - cost of dec below 90
class CostPowerFactor(Cost):
    def __init__(self, costbrackets, unitName="power factor"):
        """extreamly specific

        Args:
            costbrackets (list): length of 3, 0: cost of imp 90 to 95, 1: cost of imp above 95, 2: cost of dec below 90
            unitName (str, optional): name of the variable that cost depends on. Defaults to "power factor".
        """
        self._brackets = costbrackets
        self._unitName = unitName

    def requiredIns(self):
        return [[self._unitName, 'int', [0, 100]]]

    def calcCost(self, ins):
        cost = 0
        pf = ins[self._unitName]
        if pf == 90:
            return cost
        if pf > 90:
            a = pf - 90
            a = a if a < 5 else 10
            cost += self._brackets[0] * a
        if pf > 95:
            a = pf - 95
            cost += self._brackets[1] * a
        if pf < 90:
            a = 90 - pf
            cost += self._brackets[3] * a

        return cost


class BasicCat:
    def __init__(self, descriptor, costs):
        self._desc = descriptor
        self._costs = costs

    def __repr__(self):
        return self._desc

    def requiredIns(self):
        return self._costs.requiredIns()

    def calcCost(self, ins):
        return self._costs.calcCost(ins)


RGP = BasicCat("RGP : Residential General Purpose",
               CostPerUnit({50: 3.20, 150: 3.95, theRest: 5.00}) +
               (CostPerChoice([["Single Phase", 25], ["Three Phase", 65]])
                ) * CostPerUnit({theRest: 1}, "installations")
               )

BPL = BasicCat("BPL : Below Poverty Line",
               CostPerUnit({50: 1.50, 150: 3.95, theRest: 5.00}) +
               CostPerUnit({theRest: 5}, "installations")
               )

GLP = BasicCat("GLP : General Lighting Purpose",
               CostPerUnit({200: 4.10, theRest: 480}) +
               (CostPerChoice([["Single Phase", 30], ["Three Phase", 70]])
                ) * CostPerUnit({theRest: 1}, "installations")
               )

NonRGP = BasicCat("Non-RGP : Low Tension Service for Commercial and Industrial Purpose",
                  CostPerUnit({50: 3.20, 150: 3.95, theRest: 5.00}) +
                  CostPerUnit({5: 70, 10: 90}, "kW")
                  )

LTP = BasicCat("LTP (AG) : Agriculture Service",
               CostPerUnit({theRest: 3.40}) +
               CostPerUnit({theRest: 10}, "BHP")
               )

LTMD_1 = BasicCat("LTMD-1 : Low Tension Maximum Demand for Residential Purpose",
                  CostPerUnitContract({50: 150, 30: 185, theRest: 245, -1: 350}) +
                  CostPerUnitConditional({50: 4.65, theRest: 4.80}) +
                  (CostPowerFactor([0.0015, 0.0027, 0.03])
                   * CostPerUnit({theRest: 1}))
                  )

LTMD_2 = BasicCat("LTMD-2 : Low Tension Maximum Demand for other than residential purpose",
                  CostPerUnitContract({50: 175, 30: 230, theRest: 300, -1: 425}) +
                  CostPerUnitConditional({50: 4.80, theRest: 5.00}) +
                  (CostPowerFactor([0.0015, 0.0027, 0.03])
                   * CostPerUnit({theRest: 1}))
                  )

SL = BasicCat("SL : Low Tension Tension Street Light Service",
              CostPerUnit({theRest: 4.30})
              )

LEV = BasicCat("LEV : LT- Electric Vehicle Charging Stations",
               CostPerUnit({theRest: 4.20}) +
               CostPerUnit({theRest: 25}, "installations")
               )

TMP = BasicCat("TMP : Low Tension Temporary Supply ",
               CostPerUnit({theRest: 5.10}) +
               (CostPerUnit({theRest: 25}, "kW") *
                CostPerUnit({theRest: 1}, "days"))
               )

# wording on HTDM1 confused me a bit
HTDM_1 = BasicCat("HTMD-1 : High Tension Maximum Demand",
                  CostPerUnit({400: 4.55, theRest: 4.45}) +
                  CostPerUnitContract({1000: 260, theRest: 335, -1: 385}) +
                  (CostPowerFactor([0.0015, 0.0027, 0.03]) * CostPerUnit({theRest: 1})) +
                  CostPerUnitConditional({300: 0.80, theRest: 1.00}) +
                  CostPerUnit({theRest: 0.30})
                  )

HTDM_2 = BasicCat("HTMD-2 : High Tension Water and Sewage Pumping Stations run by AMC",
                  CostPerUnit({theRest: 4.10+0.60+0.30}) +
                  CostPerUnitContract({theRest: 225, -1: 285}) +
                  (CostPowerFactor([0.0015, 0.0027, 0.03])
                   * CostPerUnit({theRest: 1}))
                  )

HTDM_3 = BasicCat("HTMD-3 : High Tension Maximum Demand Temporary Supply",
                  CostPerUnit({theRest: 7.05+0.60}) +
                  CostPerUnitContract({theRest: 25, -1: 5}) +
                  (CostPowerFactor([0.0015, 0.0027, 0.03])
                   * CostPerUnit({theRest: 1}))
                  )

EV = BasicCat("EV: HT- Electric Vehicle Charging Stations",
              CostPerUnit({theRest: 4.10}) +
              CostPerUnitContract({theRest: 25, -1: 25})
              )

HTDM = BasicCat("HTMD - Metro Traction",
                CostPerUnit({theRest: 3.55+0.60+0.30}) +
                CostPerUnitContract({theRest: 335, -1: 50}) +
                (CostPowerFactor([-0.0015, -0.0027, 0.03])
                 * CostPerUnit({theRest: 1}))
                )

powercats = (RGP, BPL, GLP, NonRGP, LTP, LTMD_1, LTMD_2, SL, LEV,
             TMP, HTDM_1, HTDM_2, HTDM_3, EV, HTDM)
