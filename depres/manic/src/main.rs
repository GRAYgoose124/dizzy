use std::collections::HashMap;
use std::sync::Arc;

pub type ServiceFn = Arc<dyn Fn(Vec<String>) -> String + Send + Sync>;

pub struct Service {
    name: String,
    service_fn: ServiceFn,
    dependencies: Vec<String>,
}

pub struct Resolver {
    services: HashMap<String, Service>,
    results: HashMap<String, String>,
}

impl Resolver {
    pub fn new(services: Vec<Service>) -> Resolver {
        let services = services.into_iter().map(|s| (s.name.clone(), s)).collect();
        Resolver {
            services,
            results: HashMap::new(),
        }
    }

    pub fn resolve(&mut self, service_name: &str) -> String {
        if let Some(result) = self.results.get(service_name) {
            return result.clone();
        }

        let (service_fn, dependency_names) = {
            let service = self.services.get(service_name).expect("Unknown service");
            (service.service_fn.clone(), service.dependencies.clone())
        };

        let dependency_results = dependency_names
            .into_iter()
            .map(|dep| self.resolve(&dep))
            .collect();

        let result = service_fn(dependency_results);
        self.results
            .insert(service_name.to_string(), result.clone());
        result
    }
}

fn main() {
    // let service_a = Service {
    //     name: "ServiceA".to_string(),
    //     service_fn: Arc::new(|_| "Result A".to_string()),
    //     dependencies: vec![],
    // };

    // let service_b = Service {
    //     name: "ServiceB".to_string(),
    //     service_fn: Arc::new(|results| format!("Result B ({})", results.join(", "))),
    //     dependencies: vec!["ServiceA".to_string()],
    // };

    // let service_c = Service {
    //     name: "ServiceC".to_string(),
    //     service_fn: Arc::new(|results| format!("Result C ({})", results.join(", "))),
    //     dependencies: vec!["ServiceA".to_string(), "ServiceB".to_string()],
    // };
    let service_a = Service {
        name: "ServiceA".to_string(),
        service_fn: Arc::new(|_| {
            println!("Running ServiceA");
            "Result A".to_string()
        }),
        dependencies: vec![],
    };

    let service_b = Service {
        name: "ServiceB".to_string(),
        service_fn: Arc::new(|results| {
            println!("Running ServiceB");
            format!("Result B ({})", results.join(", "))
        }),
        dependencies: vec!["ServiceA".to_string()],
    };

    let service_c = Service {
        name: "ServiceC".to_string(),
        service_fn: Arc::new(|results| {
            println!("Running ServiceC");
            format!("Result C ({})", results.join(", "))
        }),
        dependencies: vec!["ServiceA".to_string(), "ServiceB".to_string()],
    };

    let mut resolver = Resolver::new(vec![service_a, service_b, service_c]);
    let result = resolver.resolve("ServiceC");
    println!("{}", result);
}
