# -*- coding: utf-8 -*-
"""
CRD Fund Check
Developed by: Alex Skotnicki
Version 1.2
Created: 18/01/2021
Last Edited: 12/03/2021
"""
#Import relevant packages
import numpy as np
import pandas as pd

class CompareCRD:
    
    """Object to transform loaded data, and compare the changes in fund lists between two sets of Charles River 
    Holdings Data"""
    
    def __init__(self, current_excel, current_sheet, previous_excel, previous_sheet):
        self.current_excel = current_excel
        self.current_sheet = current_sheet
        self.current = self._current_df()
        
        self.previous_excel = previous_excel
        self.previous_sheet = previous_sheet
        self.previous = self._previous_df()
        
        self.current_units = self._current_units()
        self.previous_units = self._previous_units()
        
    def _current_df(self):
        return pd.read_excel(self.current_excel, self.current_sheet)
    
    def _previous_df(self):
        return pd.read_excel(self.previous_excel, self.previous_sheet)
    
    def _current_units(self):
        units = self.current[(self.current.SEC_TYP_CD=='UNIT') | (self.current.SEC_TYP_CD == 'UNITA')]
        units['interfunding_code'] = units.ACCT_CD.astype(str) + ' ' + units.EXT_SEC_ID.astype(str)
        units = units[['ACCT_CD','EXT_SEC_ID','interfunding_code']]
        units.columns = ['child','parent','interfunding_code']
        units['parent'] = units.child.str.replace(r'UT$','')
        units['interfunding_code'] = units.interfunding_code.str.replace(r'UT$','')
        
        return units
    
    def _previous_units(self):
        units = self.previous[(self.previous.SEC_TYP_CD=='UNIT') | (self.previous.SEC_TYP_CD == 'UNITA')]
        units['interfunding_code'] = units.ACCT_CD.astype(str) + ' ' + units.EXT_SEC_ID.astype(str)
        units = units[['ACCT_CD','EXT_SEC_ID','interfunding_code']]
        units.columns = ['child','parent','interfunding_code']
        units['parent'] = units.child.str.replace(r'UT$','')
        units['interfunding_code'] = units.interfunding_code.str.replace(r'UT$','')
        
        return units

    def new_funds(self):
        new_funds = []
        
        for i in self.current['ACCT_CD'].unique() :
            if i not in self.previous['ACCT_CD'].unique() :
                new_funds.append(i)
                
        return new_funds
    
    def terminated_funds(self):
        terminated_funds = []
        
        for i in self.previous['ACCT_CD'].unique() :
            if i not in self.current['ACCT_CD'].unique() :
                terminated_funds.append(i)
                
        return terminated_funds
    
    def total_new_interfund_rels(self):
        new_interfunds = []
        
        for i in self.current_units['interfunding_code'].unique():
            if i not in self.previous_units['interfunding_code'].unique():
                new_interfunds.append(i)
                
        return new_interfunds 
    
    def total_terminated_interfund_rels(self):
        terminated_interfunds = []
        
        for i in self.previous_units['interfunding_code'].unique():
            if i not in self.current_units['interfunding_code'].unique():
                terminated_interfunds.append(i)
                
        return terminated_interfunds
    
    def new_fund_interfunds(self):
        """This function returns a list of new interfunding relationships that have occurred because of the creation 
        of a new parent fund"""
        
        input_one = self.total_new_interfund_rels()
        input_two = self.new_funds()
        
        output = [i for e in input_two for i in input_one if e in i]
        
        return output
    
    def terminated_fund_interfunds(self):
        """This function returns a list of terminated interfunding relationships that have occurred because of the
        termination of the old parent fund"""
        
        input_one = self.total_terminated_interfund_rels()
        input_two = self.terminated_funds()
        
        output = [i for e in input_two for i in input_one if e in i]
        
        return output
    
    def other_new_interfunds(self):
        """This function returns a list of new interfunding relationships that are not explaied by new parent fund
        creation"""
        input_one = self.total_new_interfund_rels()
        input_two = self.new_fund_interfunds()
        
        output = [b for b in input_one if
          all(a not in b for a in input_two)]
        
        return output
    
    def other_term_interfunds(self):
        """This function returns a list of old interfunding relationships that are not explained by parent fund
        termination"""
        input_one = self.total_terminated_interfund_rels()
        input_two = self.terminated_fund_interfunds()
        
        output = [b for b in input_one if
          all(a not in b for a in input_two)]
        
        return output
    
    def summary_new_funds(self):
        """This function returns a dataframe of new funds created along with a blank comments section"""
        df = pd.DataFrame(self.new_funds(),columns=['fund_code'])
        df['comments'] = ''
        df['change_management_required'] = ''
        df.set_index('fund_code',inplace=True)
        
        return df
    
    def summary_terminated_funds(self):
        """This function returns a dataframe of new funds created along with a blank comments section"""
        df = pd.DataFrame(self.terminated_funds(),columns=['fund_code'])
        df['comments'] = ''
        df['change_management_required'] = ''
        df.set_index('fund_code',inplace=True)
        
        return df
    
    def summary_interfunding(self):
        """This function returns a dataframe with interfunding relationship changes and blank comments section"""
        df_new = pd.DataFrame(self.new_fund_interfunds(),columns=['interfunding_code'])
        df_new[['child','parent']] = df_new.interfunding_code.str.split(' ', n=1, expand=True)
        df_new['reason'] = 'new fund creation'
        
        df_new_oth = pd.DataFrame(self.other_new_interfunds(),columns=['interfunding_code'])
        df_new_oth[['child','parent']] = df_new_oth.interfunding_code.str.split(' ', n=1, expand=True)
        df_new_oth['reason'] = 'new interfunding relationship'
        
        df_term = pd.DataFrame(self.terminated_fund_interfunds(),columns=['interfunding_code'])
        df_term[['child','parent']] = df_term.interfunding_code.str.split(' ', n=1, expand=True)
        df_term['reason'] = 'old fund terminated'
        
        df_term_oth = pd.DataFrame(self.other_term_interfunds(),columns=['interfunding_code'])
        df_term_oth[['child','parent']] = df_term_oth.interfunding_code.str.split(' ', n=1, expand=True)
        df_term_oth['reason'] = 'old interfunding relationship'
        
        df_all = pd.concat([df_new, df_new_oth, df_term, df_term_oth])
        df_all.set_index('interfunding_code',inplace=True)
        df_all['comments'] = ''
        df_all['change_management_required'] = ''
        
        return df_all