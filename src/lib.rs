#![cfg_attr(windows, feature(abi_vectorcall))]
use ext_php_rs::prelude::*;
use ext_php_rs::types::Zval;
use ext_php_rs::flags::DataType;
use ext_php_rs::ffi::{zend_execute_data, zval};
use std::ffi::CStr;

#[php_function]
pub fn type_runner(name: &str) -> String {
    format!("Type runner: {}!", name)
}

pub fn zval_to_string(zv: &Zval) -> String {
    match zv.get_type() {
        DataType::Undef => "undefined".to_string(),
        DataType::Null => "null".to_string(),
        DataType::False => "bool".to_string(),
        DataType::True => "bool".to_string(),
        DataType::Long => "long".to_string(),
        DataType::Double => "double".to_string(),
        DataType::String => "string".to_string(),
        DataType::Array => "array".to_string(),
        DataType::Object(_) => zv
            .object()
            .and_then(|obj| obj.get_class_name().ok())
            .unwrap_or_else(|| "object".to_string()),
        DataType::Resource => "resource".to_string(),
        DataType::Reference => "reference".to_string(),
        DataType::Indirect => "indirect".to_string(),
        DataType::Callable => "callable".to_string(),
        DataType::ConstantExpression => "constant expression".to_string(),
        DataType::Void => "void".to_string(),
        DataType::Bool => "bool".to_string(),
        DataType::Ptr => "pointer".to_string(),
        DataType::Iterable => "iterable".to_string(),
        _ => "unknown".to_string(),
    }
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

    // Only capture non-standard functions (ZEND_USER_FUNCTION = 2)
    let type_ = unsafe { (*func).type_ };
    if type_ != 2 {
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

    // Skipping Symfony functions
    if let Some(ref class_name) = class_name {
        if class_name.starts_with("Symfony\\") {
            return;
        }
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


    let num_args = unsafe { (*execute_data).This.u2.num_args };
    let mut args = Vec::new();

    let first_arg_ptr = unsafe {execute_data.add(1) as *mut zval};
    // Arguments are stored after the zend_execute_data structure on the stack
    for i in 0..num_args {
        // Move the pointer forward by exactly 1 zend_execute_data unit, 
        // then treat that memory location as a zval.
        let arg_ptr = unsafe { first_arg_ptr.add(i as usize)};
        let val = unsafe { &*(arg_ptr as *const Zval) };
        args.push(zval_to_string(val));
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
