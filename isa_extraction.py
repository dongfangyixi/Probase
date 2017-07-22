# -*- coding:utf-8 -*-


import re

class Isa_extraction(object):
    
    #ambg=ambiguous
    '''
    parm:
    super_concept_rate_thrd: threshold used in super concept detection to decide 
                             whether or not there is a super concept in the sentence

    sub_concept_scope_thrd: threshold used in sub concept detection to decide the 
                            valuable scope of Ys

    dif_rate: used in sub concept detection when apply the first order methods.

    sub_global_rate: used in sub concept detection when apply the first order methods

    sub_ambg_thrd: used in sub-concept detection when ambiguous word occured

    pattern: python re.compile object used in syntactic_extraction to find keywords
    
    sub_concept_detection_option: 'threshold' or 'first_order' decide the method when 
                                  find the boundary of sub-concept words.
    '''
    def __init__(self,super_concept_rate_thrd,
                 sub_concept_scope_thrd,dif_rate,
                 sub_global_rate,sub_ambg_thrd,
                 pattern,
                 sub_concept_detect_option='threshold',
                 Theta=0.01):
        self.isa_dict={}
        #isa_dict's structure is {x0:{y0:num,y1:num},x1:{y0:num,y1:num} , ,}
        #self.template=
        self.super_concept_rate_thrd=super_concept_rate_thrd
        self.sub_concept_scope_thrd=sub_concept_scope_thrd
        self.dif_rate=dif_rate
        self.sub_global_rate=sub_global_rate
        self.pattern=pattern
        self.sentence_punc_pattern=re.compile(u'[,.，。]')
        self.sub_context_punc_pattern=re.compile(u'[、，]')
        self.delimiters=re.compile(u'和')
        self.super_keywords=[u'比如：',u'包括：',u'例如：',u'如：',u'叫做',u'特别是']
        self.sub_ambg_thrd=sub_ambg_thrd
        self.sub_concept_detect_option=sub_concept_detect_option 
        self.Theta=Theta
    ########################################
    #isa_dic monitor
    ####################################
    def _get_isa_dic_len(self):
        length=0
        for values in self.isa_dict.values():
            
            for v in values.values():
                #print v
                length+=v
        return length
    def _get_isa_dic_kind(self):
        num=0
        for values in self.isa_dict.values():
            num+=len(values)
        return num
    ###########################################
    #step 1.  syntactic_extraction based on rule
    ############################################
    def syntactic_extraction(self,sentence_np):
        text=sentence_np[0]
        index,key_word_model=self._hearst_pattern_matching(text,self.pattern)
        #self._set_model(key_word_model)
        if index==0:
            return [],[]
        # not consider two or more index in the text
        #Ys: [[y0],[y1_ambg0,y1_ambg1,y1_ambg2],[y2],[y3],[y4_ambg0,y4_ambg1]]
        if key_word_model=='super_sub':
            super_text=text[:index[0]]
            sub_text=text[index[1]:]
        else:
            sub_text=text[:index[0]]
            super_text=text[index[1]:]
        Xs=self._extract_super_concept(text,key_word_model,index,sentence_np[1])
        #print 'sub_text',sub_text.encode('utf-8')
        #Ys=self._extract_sub_concept(sub_text)
        Ys=self._extract_sub_np_concept(text,key_word_model,index,sentence_np[1])
        if key_word_model=='sub_super':
            Ys.reverse()
        return Xs,Ys
    def _set_model(self,model):
        self.model=model
    def _extract_super_concept(self,text,model,index,np_pos_list):
        Xs=[]
        if model=='super_sub':
            for pos in np_pos_list:
                if pos[1]<=index[0]:
                    x=text[pos[0]:pos[1]+1]
                    Xs.append(x)
        else:
            for pos in np_pos_list:
                if pos[0]>=index[1]:
                    x=text[pos[0]:pos[1]+1]
                    Xs.append(x)

        return Xs

    def _extract_sub_np_concept(self,text,model,index,np_pos_list):
        Ys=[]
        if model=='sub_super':
            for pos in np_pos_list:
                if pos[1]<=index[0]:
                    y=text[pos[0]:pos[1]+1]
                    Ys.append([y])
        else:
            for pos in np_pos_list:
                if pos[0]>=index[1]:
                    y=text[pos[0]:pos[1]+1]
                    Ys.append([y])

        return Ys
    def _extract_sub_concept(self,sub_text):
        #sentence=self.sentence_punc_pattern.split(sub_text)[0]
        elems=self.sub_context_punc_pattern.split(sub_text)
        Ys=[]
        for elem in elems:
            elem=self.delimiters.split(elem)
            Ys.append(elem)
        return Ys

    def _hearst_pattern_matching(self,text,pattern):
        #print 'text',text.encode('utf-8')
        keywords_iter=pattern.finditer(text)
        index_list=[]
        keyword_list=[]
        for k in keywords_iter:
            index_list.append(k.span())
            keyword_list.append(k.group())
        #print len(keyword_list)
        if len(keyword_list)!=1:
            return 0,0
        keyword=keyword_list[0]
        #print keyword.encode('utf-8')
        index=index_list[0]
        #print index
        if keyword in self.super_keywords:
            model='super_sub'
        else:
            model='sub_super'
        #print index
        #print model
        return index,model
    ########################################
    #step 2. super_concept detection
    #######################################
    def super_concept_detection(self,Xs,Ys):
        assert(len(Xs)>1)
        max_prob=0
        second_max_prob=0
        prob_containor=[[0,None],[0,None]]
        re=None
        Ys=self._flat(Ys)
        pair_list_len=self._get_isa_dic_len()
        #print pair_list_len
        if pair_list_len==0:
            return re,0,'pair_length=0'
        x1=None
        for x in Xs:
            prob_x=self._calculate_condition_prob(x,Ys,pair_list_len)
            #print prob_x
            if prob_containor[0][0]<prob_x:
                prob_containor[0][0]=prob_x
                prob_containor[0][1]=x
                prob_containor.sort(key=lambda x:x[0])
                #second_max_prob=max_prob
                #max_prob=prob_x
                #x1=x
        max_prob=prob_containor[1][0]
        second_max_prob=prob_containor[0][0]
        x1=prob_containor[1][1]
        if max_prob==0:
            return None,0,'max_prob=0'
        if second_max_prob==0:
            #print 'x1'
            return x1,max_prob,'sencond_prob=0'
        rate=max_prob/second_max_prob#self._calculate_super_concept_rate(x1,x2,Ys)
        if rate>self.super_concept_rate_thrd:
            re=x1
            #print 'x1x2'
        return re,max_prob,str(rate)
        
    def _max_two(self,elem_list,condition_list,pair_list_len,func):
        prob_containor=[[0,None],[0,None]]
        for x in elem_list:
            prob_x=func(x,condition_list,pair_list_len)
            #print prob_x
            if prob_containor[0][0]<prob_x:
                prob_containor[0][0]=prob_x
                prob_containor[0][1]=x
                prob_containor.sort(key=lambda x:x[0])
                #second_max_prob=max_prob
                #max_prob=prob_x
                #x1=x
        return prob_containor
    ##############################
    #step 3. sub concept detection
    ##############################
    def sub_concept_detection(self,x,Ys):
        pair_list_len=self._get_isa_dic_len()
        k,prob_list=self._find_sub_concept_scope(x,Ys,pair_list_len,option=self.sub_concept_detect_option)
        if k==0:
            return [],[]
        Ys=Ys[:k]
        sub_concepts,prob_l=self._cancel_ambiguous(x,Ys,prob_list)
        return sub_concepts,prob_l


    def add_to_isa_dict(self,x,sub_concepts):
        if sub_concepts:
            if x in self.isa_dict:
                for y in sub_concepts:
                    if y in self.isa_dict[x]:
                        self.isa_dict[x][y]+=1
                    else:
                        self.isa_dict[x][y]=1
            else:
                self.isa_dict[x]={}
                for y in sub_concepts:
                    self.isa_dict[x][y]=1
                    #print x.encode('utf-8')
                    #print y.encode('utf-8')

    def _flat(self,lst):
        return [val for sublist in lst for val in sublist]

    def _cancel_ambiguous(self,x,Ys,prob_list):
        sub_concepts=[]
        prob_l=[]
        for idx,elem in enumerate(Ys):
            assert(len(elem)>=1)
            if len(elem)==1:
                sub_concepts.append(elem[0])
                prob_l.append(prob_list[idx])
            else:
                prob_containor=[[0,None],[0,None]]
                for c in elem:
                    prob_c=self._calculate_sub_prob(c,x,sub_concepts)
                    if prob_c>prob_containor[0][0]:
                        prob_containor[0][0]=prob_c
                        prob_containor[0][1]=c
                        prob_containor.sort(key=lambda x:x[0])
                        #second_prob=max_prob
                        #max_prob=prob_c
                        #c2=c1
                        #c1=c
                max_prob=prob_containor[1][0]
                second_prob=prob_containor[0][0]
                c1=prob_containor[1][1]
                #c2=None
                
                if second_prob!=0:
                    rate=max_prob/second_prob
                    if rate>self.sub_ambg_thrd:
                        sub_concepts.append(c1)
                        prob_l.append(prob_list[idx])
                else:
                    if max_prob!=0:
                        sub_concepts.append(c1)
                        prob_l.append(prob_list[idx])

        return sub_concepts,prob_l

    def _calculate_sub_prob(self,c,x,sub_concepts):
        count_x=self._count(x,self.isa_dict)
        if count_x==0:
            count_x=1.
        count_cx=self._count_condition(x,c,self.isa_dict)
        prob_cx=float(count_cx)/count_x
        if prob_cx==0:
            prob_cx=self.Theta
            count_cx=1.
        prob_ycx=1.
        for y in sub_concepts:
            count_y_cx=self._count_multi_condition(x,c,y,self.isa_dict)
            prob_yc=float(count_y_cx)/count_cx
            if prob_yc==0:
                prob_yc=self.Theta
            prob_ycx*=prob_yc
            
        return prob_cx*prob_ycx


        

    def _find_sub_concept_scope(self,x,Ys,pair_list_len,option='threshold'):
        prob_list=[]
        count_x=float(self._count(x,self.isa_dict))
        if count_x==0.:
            count_x=1.
        for index,ys in enumerate(Ys):
            max_ambg_prob=0.
            for ys_elem in ys:
                ys_nb=self._count_condition(x,ys_elem,self.isa_dict)
                prob_ys_elem=float(ys_nb)/count_x
                if prob_ys_elem==0:
                    prob_ys_elem=self.Theta
                if max_ambg_prob<prob_ys_elem:
                    max_ambg_prob=prob_ys_elem
            prob_list.append(max_ambg_prob)
        k=self._decide_index_of_scope(prob_list,option=option)
        return k,prob_list[:k]

    def _decide_index_of_scope(self,prob_list,option='threshold'):
        #threshold?
        #first order?
        #print prob_list
        # choice one method blow:
        if option=='threshold':
            k=self._index_of_list_upto_thrd(prob_list,self.sub_concept_scope_thrd)
        elif option=='first_order':
            k=self._index_of_list_upto_first_order(prob_list,self.dif_rate,self.sub_global_rate)
        else:
            print 'wrong option, k is set to one'
            k=1
        if k==0:
            k=1
        return k
        
    def _index_of_list_upto_first_order(self,list,dif_rate,global_thrd):
        if max(list)<global_thrd:
            return 0
        dif_thrd=dif_rate*(max(list)-min(list))
        first_order_list=self._first_order(list)
        for ind,elem in enumerate(first_order_list):
            if elem>dif_thrd:
                return ind
        return len(first_order_list)
        

    def _first_order(self,list):
        first_order_list=[]
        for i in xrange(len(list)-1):
            first_order_list.append(list[i+1]-list[i])
        return first_order_list
    def _index_of_list_upto_thrd(self,list,thrd):
        index=0
        prob=list[index]
        list.append(0.)
        while prob>thrd and index<len(list):
            index+=1
            prob=list[index]
        #if index==-1:
        #    index=0
        
        return index
        
    '''
    def _calculate_super_concept_rate(self,x1,x2,Ys):
        prob_x1=self._calculate_condition_prob(x1,Ys)
        prob_x2=self._calculate_condition_prob(x2,Ys)
        rate=prob_x1/prob_x2
        return rate
    '''
    def _calculate_condition_prob(self,x,Ys,pair_list_len):
        count_x=self._count(x,self.isa_dict)
        prob_x=count_x/pair_list_len
        if prob_x==0:
            prob_x=self.Theta
            count_x=1.
        prob_condition=1.
        for y in Ys:
            count_xy=float(self._count_condition(x,y,self.isa_dict))
            prob_xy=float(count_xy)/count_x
            if prob_xy==0:
                prob_xy=self.Theta
            prob_condition*=prob_xy
        prob=prob_x*prob_condition
        return prob

    def _count(self,term,pair_dict):
        count=0
        '''
        place_dic={'super':0,'sub':1}
        try:
            index=place_dic[place]
        except:
            print('Place in a pair is super or sub')
            raise
        '''
        if term in pair_dict:
            #tmp=pair_dict[term].values()
            #print tmp
            #print len(tmp)
            count=sum(pair_dict[term].values())
        '''
        for pair in pair_list:
            if term==pair[index]:
                count+=1
        '''
        #if count==0:
        #    count=0.01
        #    print count
        return count
    def _count_condition(self,super_term,sub_term,pair_dict):
        count=0
        if super_term in pair_dict:
            if sub_term in pair_dict[super_term]:
                count=pair_dict[super_term][sub_term]
        '''
        for pair in pair_dict:
            if super_term==pair[0] and sub_term==pair[1]:
                count+=1
        '''
        #if count==0:
        #    count=0.01
        #    print count
        return count
    def _count_multi_condition(self,super_term,c,y,pair_dict):
        count=0
        if super_term in pair_dict:
            if c in pair_dict[super_term]:
                if y in pair_dict[super_term]:
                    count=pair_dict[super_term][y]
        #if count==0:
        #    count=0.01
        #    print count
        return count
        
