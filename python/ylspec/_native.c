/* Copyright 2026 Cavanşir Qurbanzadə. SPDX-License-Identifier: Apache-2.0 */
#define PY_SSIZE_T_CLEAN
#define Py_LIMITED_API 0x030B0000
#include <Python.h>
#include "ylspec.h"
#include <string.h>
#include <stdlib.h>

static PyObject *raise_error(yl_error *e){
    PyObject *args=Py_BuildValue("(isKKKs)",(int)e->code,yl_status_name(e->code),(unsigned long long)e->offset,(unsigned long long)e->line,(unsigned long long)e->column,e->message);
    if(args){PyErr_SetObject(PyExc_ValueError,args);Py_DECREF(args);}return NULL;
}
static PyObject *to_python(const yl_value *v){
    PyObject *r=NULL,*x,*k;size_t i,n;const char *s;
    switch(yl_value_type(v)){
    case YL_STRING:s=yl_value_text(v,&n);return PyUnicode_DecodeUTF8(s,(Py_ssize_t)n,"strict");
    case YL_INTEGER:return PyLong_FromLongLong(yl_value_integer(v));
    case YL_FLOAT:return PyFloat_FromDouble(yl_value_float(v));
    case YL_BOOLEAN:return PyBool_FromLong(yl_value_boolean(v));
    case YL_TEMPORAL:s=yl_value_text(v,&n);return Py_BuildValue("(sy#)",yl_temporal_kind(v),s,(Py_ssize_t)n);
    case YL_ARRAY:
        r=PyList_New(0);if(!r)return NULL;
        for(i=0;i<yl_count(v);i++){x=to_python(yl_at(v,i));if(!x||PyList_Append(r,x)){Py_XDECREF(x);Py_DECREF(r);return NULL;}Py_DECREF(x);}return r;
    case YL_TABLE:
        r=PyDict_New();if(!r)return NULL;
        for(i=0;i<yl_count(v);i++){s=yl_key(v,i,&n);k=PyUnicode_DecodeUTF8(s,(Py_ssize_t)n,"strict");x=to_python(yl_at(v,i));if(!k||!x||PyDict_SetItem(r,k,x)){Py_XDECREF(k);Py_XDECREF(x);Py_DECREF(r);return NULL;}Py_DECREF(k);Py_DECREF(x);}return r;
    }PyErr_SetString(PyExc_TypeError,"Unknown native type");return NULL;
}
static yl_value *from_python(PyObject *obj,unsigned depth,yl_error *e){
    yl_value *v=NULL,*child;PyObject *x,*key,*encoded;Py_ssize_t pos=0,n,i;const char *s;yl_status status;
    if(depth>128){PyErr_SetString(PyExc_ValueError,"Maximum construction depth exceeded");return NULL;}
    if(PyBool_Check(obj))v=yl_boolean(obj==Py_True);
    else if(PyLong_Check(obj)){long long number=PyLong_AsLongLong(obj);if(PyErr_Occurred())return NULL;v=yl_integer((int64_t)number);}
    else if(PyFloat_Check(obj))v=yl_float(PyFloat_AsDouble(obj));
    else if(PyUnicode_Check(obj)){encoded=PyUnicode_AsUTF8String(obj);if(!encoded)return NULL;s=PyBytes_AsString(encoded);n=PyBytes_Size(encoded);v=yl_string(s,(size_t)n);Py_DECREF(encoded);}
    else if(PyTuple_Check(obj)&&PyTuple_Size(obj)==2){
        PyObject *kind=PyTuple_GetItem(obj,0),*text=PyTuple_GetItem(obj,1),*kb;
        if(!PyUnicode_Check(kind)||!PyBytes_Check(text)){PyErr_SetString(PyExc_TypeError,"Invalid internal temporal representation");return NULL;}
        kb=PyUnicode_AsUTF8String(kind);if(!kb)return NULL;v=yl_temporal(PyBytes_AsString(kb),PyBytes_AsString(text),(size_t)PyBytes_Size(text));Py_DECREF(kb);if(!v){PyErr_SetString(PyExc_ValueError,"Invalid temporal kind or literal");return NULL;}
    }
    else if(PyDict_Check(obj)){
        v=yl_new(YL_TABLE);if(!v)goto memory;
        while(PyDict_Next(obj,&pos,&key,&x)){
            if(!PyUnicode_Check(key)){PyErr_SetString(PyExc_TypeError,"Table keys must be strings");goto failed;}
            encoded=PyUnicode_AsUTF8String(key);if(!encoded)goto failed;
            child=from_python(x,depth+1,e);if(!child){Py_DECREF(encoded);goto failed;}
            status=yl_set(v,PyBytes_AsString(encoded),(size_t)PyBytes_Size(encoded),child,e);Py_DECREF(encoded);
            if(status){yl_value_free(child);raise_error(e);goto failed;}
        }
    }
    else if(PyList_Check(obj)){
        v=yl_new(YL_ARRAY);if(!v)goto memory;n=PyList_Size(obj);
        for(i=0;i<n;i++){x=PyList_GetItem(obj,i);child=from_python(x,depth+1,e);if(!child)goto failed;status=yl_append(v,child,e);if(status){yl_value_free(child);raise_error(e);goto failed;}}
    }
    else {PyErr_SetString(PyExc_TypeError,"Unsupported value; expected TOML-compatible data");return NULL;}
    if(!v)goto memory;return v;
memory:PyErr_NoMemory();
failed:yl_value_free(v);return NULL;
}
static PyObject *decode(PyObject *self,PyObject *args){
    const char *s;Py_ssize_t n;unsigned long long max_bytes;unsigned depth;yl_limits limits;yl_document *d=NULL;yl_error e={0};PyObject *r;(void)self;
    if(!PyArg_ParseTuple(args,"y#KI",&s,&n,&max_bytes,&depth))return NULL;
    if(max_bytes>SIZE_MAX){PyErr_SetString(PyExc_OverflowError,"Byte limit does not fit size_t");return NULL;}
    limits.max_document_bytes=(size_t)max_bytes;limits.max_depth=depth;
    if(yl_parse(s,(size_t)n,&limits,&d,&e))return raise_error(&e);
    r=to_python(yl_root(d));yl_document_free(d);return r;
}
static PyObject *encode(PyObject *self,PyObject *args){
    PyObject *obj,*r;unsigned long long max_bytes;unsigned depth;int framed;yl_limits limits;yl_value *root;yl_document *d=NULL;yl_buffer b={0};yl_error e={0};yl_status status;(void)self;
    if(!PyArg_ParseTuple(args,"OKIp",&obj,&max_bytes,&depth,&framed))return NULL;
    if(max_bytes>SIZE_MAX){PyErr_SetString(PyExc_OverflowError,"Byte limit does not fit size_t");return NULL;}
    limits.max_document_bytes=(size_t)max_bytes;limits.max_depth=depth;root=from_python(obj,0,&e);if(!root)return NULL;
    if(yl_document_create(root,&limits,&d,&e)){yl_value_free(root);return raise_error(&e);}
    status=framed?yl_pack(d,&b,&e):yl_dump(d,&b,&e);yl_document_free(d);if(status)return raise_error(&e);
    r=PyBytes_FromStringAndSize((const char*)b.data,(Py_ssize_t)b.size);yl_buffer_free(&b);return r;
}
static PyObject *unpack_native(PyObject *self,PyObject *args){
    const char *s;Py_ssize_t n;unsigned long long offset,max_bytes;unsigned depth;yl_limits limits;yl_document *d=NULL;yl_error e={0};size_t consumed;PyObject *r,*tuple;(void)self;
    if(!PyArg_ParseTuple(args,"y#KKI",&s,&n,&offset,&max_bytes,&depth))return NULL;
    if(offset>SIZE_MAX||max_bytes>SIZE_MAX){PyErr_SetString(PyExc_OverflowError,"Offset or limit does not fit size_t");return NULL;}
    limits.max_document_bytes=(size_t)max_bytes;limits.max_depth=depth;
    if(yl_unpack(s,(size_t)n,(size_t)offset,&limits,&d,&consumed,&e))return raise_error(&e);
    r=to_python(yl_root(d));yl_document_free(d);if(!r)return NULL;tuple=Py_BuildValue("(OK)",r,(unsigned long long)consumed);Py_DECREF(r);return tuple;
}
typedef struct {PyObject *callback;} reader;
static int callback_read(void *context,uint64_t offset,void *buffer,size_t size){reader *r=(reader*)context;PyObject *result=PyObject_CallFunction(r->callback,"KK",(unsigned long long)offset,(unsigned long long)size);if(!result)return -1;if(!PyBytes_Check(result)||PyBytes_Size(result)!=(Py_ssize_t)size){Py_DECREF(result);PyErr_SetString(PyExc_OSError,"read_at callback must return exactly the requested bytes");return -1;}memcpy(buffer,PyBytes_AsString(result),size);Py_DECREF(result);return 0;}
static PyObject *read_native(PyObject *self,PyObject *args){
    reader reader_context;unsigned long long offset,available,max_bytes;uint64_t consumed=0;unsigned depth;yl_limits limits;yl_document *d=NULL;yl_error e={0};PyObject *r;(void)self;
    if(!PyArg_ParseTuple(args,"OKKKI",&reader_context.callback,&offset,&available,&max_bytes,&depth))return NULL;
    if(max_bytes>SIZE_MAX){PyErr_SetString(PyExc_OverflowError,"Limit does not fit size_t");return NULL;}
    limits.max_document_bytes=(size_t)max_bytes;limits.max_depth=depth;
    if(yl_read_at(callback_read,&reader_context,offset,available,&limits,&d,&consumed,&e)){if(PyErr_Occurred())return NULL;return raise_error(&e);}
    r=to_python(yl_root(d));yl_document_free(d);return r;
}
static PyMethodDef methods[]={
    {"decode",decode,METH_VARARGS,"Parse length-bounded text with the C core."},
    {"encode",encode,METH_VARARGS,"Serialize with the C core."},
    {"unpack",unpack_native,METH_VARARGS,"Decode a bounded frame."},
    {"read_at",read_native,METH_VARARGS,"Read exactly one frame through a callback."},
    {NULL,NULL,0,NULL}
};
static struct PyModuleDef definition={PyModuleDef_HEAD_INIT,"_native","YLSpec C bindings.",0,methods,NULL,NULL,NULL,NULL};
PyMODINIT_FUNC PyInit__native(void){PyObject *m=PyModule_Create(&definition);if(m&&PyModule_AddStringConstant(m,"__version__",yl_version())){Py_DECREF(m);return NULL;}return m;}
