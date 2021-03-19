from collections import UserList
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st

class AssetList(UserList):
    yaml_tag = '!Assetlist'
    def __init__(self, name, data):
        self.name = name
        self.data = data
        return
    
    
    @classmethod
    def to_yaml(cls, dumper, mapping):
        return dumper.represent_mapping(
            cls.yaml_tag, 
            {
                'name': mapping.name
                , 'data': mapping.data
            }
        )
    
    
    @classmethod
    def from_yaml(cls, loader, node):
        value = loader.construct_mapping(node)
        return AssetList(value['name'], value['data'])
    
    
    def agg(self, f_agg, r_init=None):
        r = r_init
        for i, o in enumerate(self.data):
            if isinstance(o,Asset):
                r = f_agg(r, o)
            elif isinstance(o,AssetList):
                r = o.agg(f_agg, r)
        return r
    
    
    def get_balance_eom(self):
        
        def agg_balance_eom(r, a):
            asset_balance_sheet_df = (
                a.balance_sheet_df
                .assign(asset_name = a.params['name'])
                .reset_index()
    #             .assign(ym = lambda y: y.ym.apply(lambda x: x.strftime('%Y-%m')))
                .assign(ym = lambda y: y.ym.apply(lambda x: x.to_timestamp('M')))
                [['asset_name','ym','balance_eom']]
            )
            return pd.concat([r, asset_balance_sheet_df])

        r_init = pd.DataFrame([], columns=['asset_name','ym','balance_eom'])
        return self.agg(agg_balance_eom, r_init)
    

class Asset():
    yaml_tag = '!Asset'
    def __init__(self,name, params_asset):
        self.name = name
        self.params = params_asset
        self.params_general = params_general = {
            'inflation': 0.00
            ,'ym_end': '2040-12'
        }
        self.compute_balance_sheet()
        return
    
    def __repr__(self):
        return self.name
    
    @classmethod
    def to_yaml(cls, dumper, data):
        return dumper.represent_mapping(cls.yaml_tag, {'name': data.name, 'params': data.params})
      
    @classmethod
    def from_yaml(cls, loader, node):
        data = loader.construct_mapping(node)
        return cls(data['name'], data['params'])
    
    def st_sidebar(self):
        return 
    
    def st_main(self):
        st.subheader(self.name)
        return
    
    def compute_balance_sheet(self):
        raise NotImplementedError
        
        
        
class AccountAsset(Asset):
    yaml_tag = '!AccountAsset'
    def __init__(self, name, params_asset):
        super().__init__(name, params_asset)
        self.type = 'Interest Asset'
        return
        
    def st_sidebar(self):
        self.value = st.sidebar.slider(self.name, min_value=self.a, max_value=self.b)
        return 
    
    def st_main(self):
        with st.beta_expander(label=self.name):
#             st.subheader(self.name)
            st.text(str(self.value))
        return
        
    def compute_balance_sheet(self):
        ym_index = pd.PeriodIndex(
            pd.period_range(start = self.params['ym_start']
                            , end = self.params_general['ym_end']
                            , freq = 'M'
                           )
            , name='ym'
        )
        
        ym_interest_rates = (
            pd.DataFrame(self.params['interest_rates'])
            .rename(columns={'from_ym': 'ym', 'rate_y': 'interest_rate_y'})
            .assign(ym=lambda x: x.ym.apply(pd.Period))
            .set_index('ym')
            .reindex(ym_index, method='ffill')
            .fillna(0)
        )
        
        ym_transactions = (
            pd.DataFrame(
               pd.period_range(
                   start = self.params['transactions'][0]
                   , end = self.params['transactions'][1]
                   , freq = self.params['transactions'][2]
               )
                , columns=['ym']
            )
            .assign(transaction = self.params['transactions'][3])
            .assign(ym=lambda x: x.ym.apply(lambda y: y.asfreq('M', how='start')))
            .set_index('ym')
            .reindex(ym_index)
            .fillna(0)
        )
        
        ym_balance = (
            pd.DataFrame(
                    [[pd.Period(self.params['ym_start']), self.params['balance_start']]]
                    , columns = ['ym', 'balance_bom']
                )
                .set_index('ym')
            .reindex(ym_index)
            .join(ym_transactions)
            .join(ym_interest_rates)
            .assign(interest = np.nan)
            .assign(balance_eom = np.nan)
        )
        
        for i in range(0,ym_balance.shape[0]):
            if i > 0:
                ym_balance['balance_bom'].iloc[i] = ym_balance['balance_eom'].iloc[i-1]
            ym_balance['interest'].iloc[i] = ym_balance['balance_bom'].iloc[i] * ((1+ym_balance['interest_rate_y'].iloc[i]) ** (1/12) -1)
            ym_balance['balance_eom'].iloc[i] = ym_balance['balance_bom'].iloc[i] + ym_balance['interest'].iloc[i] + ym_balance['transaction'].iloc[i]
        
        self.balance_sheet_df = ym_balance
        
        return