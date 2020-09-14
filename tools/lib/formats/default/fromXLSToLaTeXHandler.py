from .. import *
from ...data import dataFileBase,DataType,method,excitationValue,datafileSelector,getSubtablesRange,state
from ...utils import getValFromCell
from TexSoup import TexSoup,TexNode
from ...LaTeX import newCommand,extractMath
import numpy as np
import json
import itertools
def GetTypeFromAcronym(acronym):
  if acronym=="npi":
    return r"n \rightarrow \pi^\star"
  elif acronym=="ppi":
    return r"\pi \rightarrow \pi^\star"
  elif acronym=="n3s":
    return  r"n \rightarrow 3s"
  elif acronym=="dou":
    return "double"
  elif "p3p":
    return r"\pi \rightarrow 3p"
  elif acronym=="non-d":
    return None
  else:
    raise ValueError("acronym not recognised")
def GetFullState(TexState,datatype=DataType.ABS,VR=None,typeAcronym=None,Soup=True):
  statemath=str(extractMath(TexState))
  resultstr=statemath
  fulltype=[]
  if datatype==DataType.FLUO:
    resultstr+=r"[\mathrm{F}]"
  if VR!=None:
    fulltype.append(r"\mathrm{"+VR+"}")
  if typeAcronym!=None:
    _type=GetTypeFromAcronym(typeAcronym)
    if _type!=None:
      fulltype.append(_type)
    if len(fulltype)>0:
      resultstr+=" ("+";".join(fulltype)+")"
  resultstr="$"+resultstr+"$"
  if Soup:
    return TexSoup(resultstr)
  else:
    return resultstr

@formatName("fromXLSToLaTeX")
class fromXLSToLaTeXHandler(formatHandlerBase):
  def readFromTable(self,table):
    datalist=list()
    subtablesRange=getSubtablesRange(table,firstindex=1,column=1)
    for myrange in subtablesRange:
      valDic=dict()
      mymolecule=str(table[myrange[0],1])
      initialState=self.TexOps.initialStates[mymolecule]
      for col in itertools.chain(range(8,11), range(14,np.size(table,1))):
        col=table[:,col]
        basis="aug-cc-pVTZ"
        mymethcell=list(col[0])
        if len(mymethcell)==0:
          continue
        if isinstance(mymethcell[0],TexNode) and mymethcell[0].name=="$":
          kindSoup=TexSoup("".join(list(mymethcell[0].expr.all)))
          newCommand.runAll(kindSoup,self.commands)
          kind=str(kindSoup)
          methodnameSoup=TexSoup(mymethcell[1].value)
          newCommand.runAll(methodnameSoup,self.commands)
          methodname=str(methodnameSoup)
        else:
          kind=""
          methtex=col[0]
          newCommand.runAll(methtex,self.commands)
          methodname=str(methtex)
        mymethod=method(methodname,basis)
        methkey=json.dumps(mymethod.__dict__)
        mathstates=[GetFullState(table[i,4],VR=str(table[i,6]),typeAcronym=str(table[i,7]),Soup=True) for i in myrange]
        finsts=dataFileBase.convertState(mathstates,initialState,default=self.TexOps.defaultType,commands=self.commands)
        for index,cell in enumerate(col[myrange]):
          if str(cell)!="":
            val=str(cell)
            safedat=str(table[index+myrange[0],12])
            if safedat=="Y":
              unsafe=False
            elif safedat=="N":
              unsafe=True
            else:
              ValueError("Safe value error")
            finst=finsts[index]
            dt=finst[1]
            if dt in valDic:
              dtDic=valDic[dt]
            else:
              dtDic=dict()
              valDic[dt]=dtDic
            if not methkey in dtDic:
              dtDic[methkey]=dict()
            dataDic=dtDic[methkey]
            exkey=(json.dumps(finst[0].__dict__,),finst[2])
            if not exkey in dataDic:
              dataDic[exkey]=dict()
            if kind=='':
              dataDic[exkey][kind]=(val,unsafe)
            else:
              dataDic[exkey][kind]=val
            #data.excitations.append(excitationValue(initialState,finst[0],val,type=finst[2]))
      for dt,methdic in valDic.items():
        for methstring,exdic in methdic.items():
          data=datafileSelector(dt)()
          data.molecule=mymolecule
          methdic=json.loads(methstring)
          data.method=method(methdic["name"],methdic["basis"])
          for exstr,values in exdic.items():
            stDict=json.loads(exstr[0])
            ty=exstr[1]
            st=state(stDict["number"],stDict["multiplicity"],stDict["symetry"])
            T1=values["\\%T_1"] if "\\%T_1" in values  else None
            oF= values["f"] if "f" in values  else None
            val,unsafe= values[""] if "" in values  else [None,False]
            data.excitations.append(excitationValue(initialState,st,val,type=ty,T1=T1,isUnsafe=unsafe,oscilatorForces=oF))
            datalist.append(data)
    return datalist