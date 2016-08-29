#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# This file is subject to the terms and conditions defined in
# file 'LICENSE.md', which is part of this source code package.
#

import os
import socket
from kubernetes import (
    K8sConfig,
    K8sContainer,
    K8sDeployment,
    K8sObject,
    K8sPod,
    K8sReplicationController,
    K8sSecret,
    K8sService
)
from kubernetes.K8sExceptions import NotFoundException

kubeconfig_fallback = '{0}/.kube/config'.format(os.path.abspath(os.path.dirname(os.path.realpath(__file__))))


def is_reachable(api_host):
    port = None
    s = None
    try:
        scheme, host, port = api_host.replace("//", "").split(':')
    except ValueError:  # no port specified
        scheme, host = api_host.replace("//", "").split(":")
    try:
        if port is not None:
            s = socket.create_connection((host, port), timeout=0.5)
        else:
            if scheme == 'http':
                port = 80
            elif scheme == 'https':
                port = 443
            s = socket.create_connection((host, port), timeout=0.5)
        if s is not None:
            s.close()
        return True
    except Exception as err:
        return False


def create_container(model=None, name=None, image="redis"):
    if model is None:
        obj = K8sContainer(
            name=name,
            image=image
        )
    else:
        obj = K8sContainer(model=model)
    return obj


def create_config():
    try:
        config = K8sConfig(kubeconfig=kubeconfig_fallback)
    except Exception:
        config = K8sConfig()
    return config


def create_object(config=None, name=None, obj_type=None):
    if config is None:
        config = create_config()
    obj = K8sObject(
        config=config,
        name=name,
        obj_type=obj_type
    )
    return obj


def create_pod(config=None, name=None):
    if config is None:
        config = create_config()
    obj = K8sPod(
        config=config,
        name=name
    )
    return obj


def create_rc(config=None, name=None, replicas=0):
    if config is None:
        config = create_config()
    obj = K8sReplicationController(
        config=config,
        name=name,
        replicas=replicas
    )
    return obj


def create_secret(config=None, name=None):
    if config is None:
        config = create_config()
    obj = K8sSecret(
        config=config,
        name=name
    )
    return obj


def create_service(config=None, name=None):
    if config is None:
        config = create_config()
    obj = K8sService(
        config=config,
        name=name
    )
    return obj


def create_deployment(config=None, name=None):
    if config is None:
        config = create_config()
    obj = K8sDeployment(
        config=config,
        name=name
    )
    return obj


def cleanup_objects():
    config = K8sConfig(kubeconfig=kubeconfig_fallback)
    if is_reachable(config.api_host):
        cleanup_rcs()
        cleanup_pods()
        cleanup_secrets()
        cleanup_services()


def cleanup_pods():
    ref = create_pod(name="throwaway")
    if is_reachable(ref.config.api_host):
        pods = ref.list()
        while len(pods) > 0:
            for p in pods:
                try:
                    pod = K8sPod(config=ref.config, name=p['metadata']['name']).get()
                    pod.delete()
                except NotFoundException:
                    continue
            pods = ref.list()


def cleanup_rcs():
    ref = create_rc(name="throwaway")
    if is_reachable(ref.config.api_host):
        rcs = ref.list()
        while len(rcs) > 0:
            for rc in rcs:
                try:
                    obj = K8sReplicationController(config=ref.config, name=rc['metadata']['name']).get()
                    obj.delete()
                except NotFoundException:
                    continue
            rcs = ref.list()


def cleanup_secrets():
    ref = create_secret(name="throwaway")
    if is_reachable(ref.config.api_host):
        secrets = ref.list()
        while len(secrets) > 1:
            for secret in secrets:
                try:
                    obj = K8sSecret(config=ref.config, name=secret['metadata']['name']).get()
                    if 'service-account-token' not in obj.model.model['type']:
                        obj.delete()
                except NotFoundException:
                    continue
            secrets = ref.list()


def cleanup_services():
    ref = create_service(name="throwaway")
    if is_reachable(ref.config.api_host):
        services = ref.list()
        while len(services) > 1:
            for service in services:
                try:
                    obj = K8sService(config=ref.config, name=service['metadata']['name']).get()
                    if not _is_api_server(service):
                        obj.delete()
                except NotFoundException:
                    continue
            services = ref.list()


def cleanup_deployments():
    ref = create_deployment(name="throwaway")
    if is_reachable(ref.config.api_host):
        deps = ref.list()
        while len(deps) > 0:
            for d in deps:
                try:
                    obj = K8sDeployment(config=ref.config, name=d['metadata']['name']).get()
                    obj.delete()
                except NotFoundException:
                    continue
            deps = ref.list()


def _is_api_server(service=None):
    if not isinstance(service, dict):
        return False
    if 'metadata' not in service:
        return False
    if 'labels' not in service['metadata']:
        return False
    if 'component' not in service['metadata']['labels']:
        return False
    if 'provider' not in service['metadata']['labels']:
        return False
    if 'apiserver' != service['metadata']['labels']['component']:
        return False
    if 'kubernetes' != service['metadata']['labels']['provider']:
        return False
    return True
