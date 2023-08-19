use std::cell::RefCell;
use std::collections::HashMap;
use std::sync::Arc;

pub type ServiceFn = Arc<dyn Fn(Vec<String>, &mut HashMap<String, String>) -> String + Send + Sync>;

pub struct Service {
    name: String,
    service_fn: ServiceFn,
    dependencies: Vec<String>,
}

impl Service {
    // new function to create a service with a logging wrapper
    pub fn new(name: String, service_fn: ServiceFn, dependencies: Vec<String>) -> Service {
        Service {
            name,
            service_fn,
            dependencies,
        }
    }

    // function to execute the service
    pub fn execute(&self, args: Vec<String>, context: &mut HashMap<String, String>) -> String {
        println!("Running {}", self.name);
        (self.service_fn)(args, context)
    }
}

pub struct Resolver {
    services: HashMap<String, Service>,
    results: RefCell<HashMap<String, String>>,
}

impl Resolver {
    pub fn new(services: Vec<Service>) -> Resolver {
        let services = services.into_iter().map(|s| (s.name.clone(), s)).collect();
        Resolver {
            services,
            results: RefCell::new(HashMap::new()),
        }
    }

    pub fn resolve(&self, service_name: &str, context: &mut HashMap<String, String>) -> String {
        if let Some(result) = self.results.borrow().get(service_name) {
            return result.clone();
        }

        let service = self
            .services
            .get(service_name)
            .expect("Unknown service")
            .clone();

        let mut dependency_results = Vec::new();
        for dep in service.dependencies.iter() {
            dependency_results.push(self.resolve(dep, context));
        }

        let result = service.execute(dependency_results, context);
        self.results
            .borrow_mut()
            .insert(service_name.to_string(), result.clone());
        result
    }
}

fn main() {
    let service_a = Service::new(
        "ServiceA".to_string(),
        Arc::new(|_, _| "Result A".to_string()),
        vec![],
    );

    let service_b = Service::new(
        "ServiceB".to_string(),
        Arc::new(|results, _| format!("Result B ({})", results.join(", "))),
        vec!["ServiceA".to_string()],
    );

    let service_c = Service::new(
        "ServiceC".to_string(),
        Arc::new(|results, _| format!("Result C ({})", results.join(", "))),
        vec!["ServiceA".to_string(), "ServiceB".to_string()],
    );

    let resolver = Resolver::new(vec![service_a, service_b, service_c]);
    let mut context = HashMap::new();
    let result = resolver.resolve("ServiceC", &mut context);
    println!("{}", result);
}
