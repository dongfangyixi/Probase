# -*- coding:utf-8 -*-
from isa_extraction import Isa_extraction
#from prepare_data import TEMPLATE
import re
import cPickle
from tqdm import tqdm
TEMPLATE=u'比如：|包括：|例如：|是一个|是一种|特别是|如：|叫做'
key_word_pattern=re.compile(TEMPLATE)

data=cPickle.load(open('../data/np_result.pkl','rb'))
#OPTION='first_order'
OPTION='threshold'
extraction=Isa_extraction(super_concept_rate_thrd=1.1,
                          sub_concept_scope_thrd=0.01,
                          dif_rate=0.5,
                          sub_global_rate=0.01,
                          sub_ambg_thrd=1.1,
                          pattern=key_word_pattern,
                          sub_concept_detect_option=OPTION)
kind_num_prev=0
kind_num=1
epoch=0
af=open('../data/analysis_iter.txt','w')
saf=open('../data/analysis_selected_iter.txt','w')
while kind_num_prev!=kind_num:
    af.writelines('epoch: '+str(epoch)+'\n~~~~~~~~~~\n\n')
    count=0
    for sentence in tqdm(data):
        count+=1
        #sentence=data[0]
        Xs,Ys=extraction.syntactic_extraction(sentence)
        #print 'Xs: ',u'-'.join(Xs).encode('utf-8')
        #print 'Ys: ',u'-'.join(extraction._flat(Ys)).encode('utf-8')
        flat_Ys=extraction._flat(Ys)
        if epoch==0:
            if  len(Xs)==1 and len(Ys)==1:
                #print 'hit!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
                extraction.add_to_isa_dict(Xs[0],Ys[0])
                #print 'unic x:',Xs[0].encode('utf-8')
                #print 'unic y:',Ys[0][0].encode('utf-8')
                #print extraction._get_isa_dic_len()
        else:
            af.writelines(str(count)+'. '+'\n')
            af.writelines('sentence: '+sentence[0].encode('utf-8')+'\n\n')
            af.writelines('Xs list: \n')
            af.writelines('\n'.join(Xs).encode('utf-8')+'\n-------\n')
            af.writelines('Ys list: \n')
            af.writelines('\n'.join(flat_Ys).encode('utf-8')+'\n-------\n')
            if  len(Xs)==1 and len(Ys)==1:
                #print 'hit!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
                extraction.add_to_isa_dict(Xs[0],Ys[0])
            if  len(Xs)>1:
                x,prob,rate=extraction.super_concept_detection(Xs,Ys)
                if x:
                    Xs=[x]
                    #print 'chose x:',x.encode('utf-8')
                    #print type(x)
                    af.writelines('Detected x:\n'+x.encode('utf-8')+' prob: '+str(prob)+' rate: '+rate+'\n-------\n')
                else:
                    Xs=[]
                    af.writelines('Detected x:\n'+'Nothing  prob: '+str(prob)+' rate: '+rate+'\n-------\n')
                     
            if len(Xs)==1 and len(Ys)>1 and Xs[0]!='\n':
                sub_concepts,prob_list=extraction.sub_concept_detection(Xs[0],Ys)
                if sub_concepts:
                    prob_list=[str(x) for x in prob_list]
                    sub_concepts_af=[x.encode('utf-8') for x in sub_concepts]
                    af_line=[' prob: '.join(x) for x in zip(sub_concepts_af,prob_list)]
                    af.writelines('Detected Ys:\n'+'\n'.join(af_line)+'\n-------\n')
                    extraction.add_to_isa_dict(Xs[0],sub_concepts)
                    saf.writelines(str(count)+'. '+'\n')
                    saf.writelines('sentence: '+sentence[0].encode('utf-8')+'\n\n')
                    saf.writelines('Ys list: \n')
                    saf.writelines('\n'.join(flat_Ys).encode('utf-8')+'\n-------\n')
                    saf.writelines('Detected x:\n'+Xs[0].encode('utf-8')+'\n-------\n')
                    saf_line=[' prob: '.join(x) for x in zip(sub_concepts_af,prob_list)]
                    saf.writelines('Detected Ys:\n'+'\n'.join(af_line)+'\n-------\n')
    kind_num_prev=kind_num
    kind_num=extraction._get_isa_dic_kind()
    print kind_num
    epoch+=1
    print epoch
    cPickle.dump(extraction.isa_dict,open('../data/isa_results_analysis/isa_result_ltp_epoch-'+str(epoch)+'.pkl','wb'),protocol=2)
cPickle.dump(extraction.isa_dict,open('../data/isa_result_ltp_fix.pkl','wb'),protocol=2)
af.close()
saf.close()

