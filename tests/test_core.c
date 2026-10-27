/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
#include "ylspec.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(c) do{if(!(c)){fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#c);return 1;}}while(0)
static const char sample[]="[_ylspec]\nversion='0.1'\nprofile='core.data'\nprofile_version='0.1'\n[data]\nname='Example'\nstamp=2026-10-27T12:34:56.123456789Z\nvalues=[1,true,2.5]\n";
typedef struct{const unsigned char *bytes;size_t size;uint64_t start,end;unsigned calls;} tracked;
static int read_block(void *context,uint64_t offset,void *buffer,size_t size){tracked *t=(tracked*)context;if(offset<t->start||offset>t->end||size>t->end-offset||offset>t->size||size>t->size-offset)return -1;t->calls++;memcpy(buffer,t->bytes+(size_t)offset,size);return 0;}
static yl_status profile(const yl_document *d,void *context,yl_error *e){(void)d;(void)e;(*(unsigned*)context)++;return YL_OK;}
int main(void){
    yl_document *d=NULL,*round=NULL;yl_error e={0};yl_buffer text={0},frame={0};yl_status s;size_t used,n;unsigned char *carrier;uint64_t consumed;tracked t;yl_limits l=yl_default_limits();const yl_value *data,*stamp;unsigned count=0;yl_profile custom={"xyz.example","1",profile,&count};yl_registry registry={&custom,1,NULL,0};
    CHECK(yl_parse(sample,sizeof(sample)-1,NULL,&d,&e)==YL_OK);
    CHECK(yl_validate(d,NULL,&e)==YL_OK);
    data=yl_get(yl_root(d),"data",4);stamp=yl_get(data,"stamp",5);
    CHECK(yl_value_type(stamp)==YL_TEMPORAL);
    CHECK(!strcmp(yl_value_text(stamp,&n),"2026-10-27T12:34:56.123456789Z"));
    CHECK(yl_dump(d,&text,&e)==YL_OK);CHECK(yl_parse((const char*)text.data,text.size,NULL,&round,&e)==YL_OK);yl_document_free(round);round=NULL;
    CHECK(yl_pack(d,&frame,&e)==YL_OK);CHECK(frame.size==text.size+32);
    carrier=(unsigned char*)malloc(frame.size*2+14);CHECK(carrier);memset(carrier,0xa5,7);memcpy(carrier+7,frame.data,frame.size);memcpy(carrier+7+frame.size,frame.data,frame.size);memset(carrier+7+frame.size*2,0xa5,7);
    CHECK(yl_unpack(carrier,frame.size*2+14,7,NULL,&round,&used,&e)==YL_OK);CHECK(used==frame.size);yl_document_free(round);round=NULL;
    t.bytes=carrier;t.size=frame.size*2+14;t.start=7;t.end=7+frame.size;t.calls=0;
    CHECK(yl_read_at(read_block,&t,7,frame.size,NULL,&round,&consumed,&e)==YL_OK);CHECK(t.calls==2&&consumed==frame.size);yl_document_free(round);round=NULL;
    CHECK(yl_read_at(read_block,&t,UINT64_MAX-1,32,NULL,&round,NULL,&e)==YL_FRAME);
    for(n=0;n<frame.size;n++)CHECK(yl_unpack(frame.data,n,0,NULL,&round,NULL,&e)!=YL_OK);
    frame.data[28]=1;CHECK(yl_unpack(frame.data,frame.size,0,NULL,&round,NULL,&e)==YL_UNSUPPORTED);frame.data[28]=0;
    frame.data[16]=255;frame.data[23]=255;CHECK(yl_unpack(frame.data,frame.size,0,NULL,&round,NULL,&e)==YL_LIMIT);
    l.max_document_bytes=10;CHECK(yl_parse(sample,sizeof(sample)-1,&l,&round,&e)==YL_LIMIT);
    l=yl_default_limits();l.max_depth=1;CHECK(yl_parse(sample,sizeof(sample)-1,&l,&round,&e)==YL_LIMIT);
    CHECK(yl_parse("\xff",1,NULL,&round,&e)==YL_SYNTAX);
    CHECK(!yl_temporal("date","2026-10-27 # unsafe",19));
    CHECK(yl_set((yl_value*)yl_get(yl_root(d),"_ylspec",7),"profile",7,yl_string("xyz.example",11),&e)==YL_OK);
    CHECK(yl_set((yl_value*)yl_get(yl_root(d),"_ylspec",7),"profile_version",15,yl_string("1",1),&e)==YL_OK);
    CHECK(yl_validate(d,NULL,&e)==YL_UNSUPPORTED);CHECK(yl_validate(d,&registry,&e)==YL_OK&&count==1);
    s=yl_append((yl_value*)data,yl_root_mutable(d),&e);CHECK(s==YL_INVALID);
    free(carrier);yl_buffer_free(&frame);yl_buffer_free(&text);yl_document_free(d);puts("C core tests passed");return 0;
}
