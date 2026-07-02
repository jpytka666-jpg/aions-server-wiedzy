# AIONS host image — Packer stub (Milestone D prep)
# NOT production-ready. Customize source_image, ssh_username, and repo URL.
#
# Build (after installing packer):
#   cd runtime/host/packer
#   packer init aions-host.pkr.hcl
#   packer build -var 'repo_url=https://github.com/ORG/aions-server-wiedzy.git' aions-host.pkr.hcl

packer {
  required_plugins {
    qemu = {
      version = ">= 1.0.9"
      source  = "github.com/hashicorp/qemu"
    }
  }
}

variable "ubuntu_version" {
  type    = string
  default = "22.04"
}

variable "repo_url" {
  type    = string
  default = "https://github.com/ORG/aions-server-wiedzy.git"
}

variable "aions_user" {
  type    = string
  default = "aions"
}

locals {
  host_scripts = "${path.root}/.."
}

source "qemu" "aions_ubuntu" {
  # Replace with your Ubuntu cloud image path or download in a wrapper script.
  iso_url      = "https://cloud-images.ubuntu.com/releases/${var.ubuntu_version}/release/ubuntu-${var.ubuntu_version}-server-cloudimg-amd64.img"
  iso_checksum = "file:https://cloud-images.ubuntu.com/releases/${var.ubuntu_version}/release/SHA256SUMS"

  disk_image         = true
  output_directory   = "output-aions-host"
  disk_size          = "20480"
  format             = "qcow2"
  accelerator        = "kvm"
  headless           = true
  ssh_username       = "ubuntu"
  ssh_timeout        = "20m"
  shutdown_command   = "sudo shutdown -P now"
  qemuargs = [
    ["-m", "4096"],
    ["-smp", "2"],
  ]
}

build {
  name    = "aions-host-ubuntu"
  sources = ["source.qemu.aions_ubuntu"]

  provisioner "shell" {
    inline = [
      "sudo apt-get update",
      "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y git python3.11 python3.11-venv curl jq",
      "sudo adduser --disabled-password --gecos '' ${var.aions_user} || true",
    ]
  }

  provisioner "file" {
    source      = local.host_scripts
    destination = "/tmp/aions-host-scripts"
  }

  provisioner "shell" {
    inline = [
      "sudo mkdir -p /usr/local/lib/aions/host",
      "sudo cp /tmp/aions-host-scripts/*.sh /usr/local/lib/aions/host/",
      "sudo chmod +x /usr/local/lib/aions/host/*.sh",
      "sudo /usr/local/lib/aions/host/install_aions_host.sh",
      "sudo -u ${var.aions_user} /usr/local/lib/aions/host/first_boot_setup.sh",
      "sudo /usr/local/lib/aions/host/validate_install.sh --user ${var.aions_user}",
    ]
  }

  provisioner "shell" {
    inline = [
      "sudo git clone --depth 1 ${var.repo_url} /opt/aions/repo || true",
      "sudo chown -R ${var.aions_user}:${var.aions_user} /opt/aions/repo || true",
    ]
  }

  provisioner "shell" {
    only_if = "test -f /opt/aions/repo/requirements-linux.txt"
    inline = [
      "sudo -u ${var.aions_user} bash -lc 'cd /opt/aions/repo && python3.11 -m venv ~/aions/venv && ~/aions/venv/bin/pip install -r requirements-linux.txt'",
      "sudo /usr/local/lib/aions/host/validate_install.sh --user ${var.aions_user} --with-runtime --strict-health",
    ]
  }

  post-processor "manifest" {
    output     = "packer-manifest.json"
    strip_path = true
  }
}
