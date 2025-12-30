#![cfg_attr(windows, feature(abi_vectorcall))]
use ext_php_rs::prelude::*;
use ext_php_rs::ffi::{zend_execute_data, zval};
use std::ffi::CStr;

#[php_function]
pub fn type_runner(name: &str) -> String {
    format!("Type runner: {}!", name)
}

pub fn type_runner_internal(class_name: Option<String>, name: &str, args: Vec<String>) {
    let msg = if let Some(class_name) = class_name {
        format!("Intercepted call to {}::{}: args={:?}\n", class_name, name, args)
    } else {
        format!("Intercepted call to {}: args={:?}\n", name, args)
    };

    print!("{}", msg);
}

unsafe extern "C" fn observer_begin(execute_data: *mut zend_execute_data) {
    let func = unsafe { (*execute_data).func };
    if func.is_null() {
        return;
    }

    let func_name_ptr = unsafe { (*func).common.function_name };
    if func_name_ptr.is_null() {
        return;
    }

    let name = unsafe {
        CStr::from_ptr((*func_name_ptr).val.as_ptr() as *const _)
            .to_string_lossy()
            .into_owned()
    };

    // Avoid infinite recursion if we call things that are observed
    if name == "type_runner" || name == "type_runner_internal" {
        return;
    }

    let class_name = unsafe {
        let scope = (*func).common.scope;
        if !scope.is_null() {
            let class_name_ptr = (*scope).name;
            if !class_name_ptr.is_null() {
                Some(
                    CStr::from_ptr((*class_name_ptr).val.as_ptr() as *const _)
                        .to_string_lossy()
                        .into_owned(),
                )
            } else {
                None
            }
        } else {
            None
        }
    };

    let num_args = unsafe { (*execute_data).This.u2.num_args };
    let mut args = Vec::new();

    // Arguments are stored after the zend_execute_data structure on the stack
    for i in 0..num_args {
        let arg_ptr = unsafe {
            let offset = (size_of::<zend_execute_data>() + size_of::<zval>() - 1)
                / size_of::<zval>();
            (execute_data as *mut zval).add(offset + i as usize)
        };
        args.push(format!("{:?}", unsafe { &*arg_ptr }));
    }

    type_runner_internal(class_name, &name, args);
}

#[repr(C)]
pub struct zend_observer_fcall_handlers {
    pub begin: Option<unsafe extern "C" fn(execute_data: *mut zend_execute_data)>,
    pub end: Option<unsafe extern "C" fn(execute_data: *mut zend_execute_data, retval: *mut zval)>,
}

unsafe extern "C" fn observer_handler(_execute_data: *mut zend_execute_data) -> zend_observer_fcall_handlers {
    zend_observer_fcall_handlers {
        begin: Some(observer_begin),
        end: None,
    }
}

unsafe extern "C" {
    fn zend_observer_fcall_register(init: Option<unsafe extern "C" fn(execute_data: *mut zend_execute_data) -> zend_observer_fcall_handlers>);
}

pub fn php_module_startup() {
    unsafe {
        zend_observer_fcall_register(Some(observer_handler));
    }
}

#[php_module]
pub fn get_module(module: ModuleBuilder) -> ModuleBuilder {
    php_module_startup();
    module.function(wrap_function!(type_runner))
}
