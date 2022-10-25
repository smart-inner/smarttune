package deployment

import (
	"bytes"
	"context"
	"fmt"
	"github.com/smart-inner/smarttune/util/disk"
	"os/exec"
	"strings"
	"syscall"
	"time"
)

// TiUPComponentType Type of TiUP component
type TiUPComponentType string

const (
	TiUPComponentTypeCluster TiUPComponentType = "cluster"
)

const (
	CMDShowConfig   = "show-config"
	CMDEditConfig   = "edit-config"
	CMDReload       = "reload"
	FlagWaitTimeout = "--wait-timeout"
	CMDYes          = "--yes"
	CMDTopologyFile = "--topology-file"
)

type Manager struct {
	TiUPBinPath string
}

func genCommand(tiUPBinPath, tiUPArgs string, timeoutS int) (cmd *exec.Cmd, cancelFunc context.CancelFunc) {
	if timeoutS != 0 {
		ctx, cancel := context.WithTimeout(context.Background(), time.Duration(timeoutS)*time.Second)
		cancelFunc = cancel
		cmd = exec.CommandContext(ctx, tiUPBinPath, strings.Fields(tiUPArgs)...)
	} else {
		cmd = exec.Command(tiUPBinPath, strings.Fields(tiUPArgs)...)
		cancelFunc = func() {}
	}
	cmd.SysProcAttr = &syscall.SysProcAttr{}
	return
}

func (m *Manager) startSyncOperation(tiUPArgs string, timeoutS int, allInfo bool) (result string, err error) {
	cmd, cancelFunc := genCommand(m.TiUPBinPath, tiUPArgs, timeoutS)
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	defer cancelFunc()

	data, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("%s.\ndetail info: %s\n%s", err.Error(), stderr.String(), string(data))
	}
	if allInfo {
		return fmt.Sprintf("%s%s", string(data), stderr.String()), nil
	}
	return string(data), nil
}

func (m *Manager) ShowConfig(componentType TiUPComponentType, clusterName string,
	args []string, timeout int) (result string, err error) {

	tiUPArgs := fmt.Sprintf("%s %s %s %s %s %d %s", componentType, CMDShowConfig,
		clusterName, strings.Join(args, " "), FlagWaitTimeout, timeout, CMDYes)

	return m.startSyncOperation(tiUPArgs, timeout, false)
}

func (m *Manager) EditConfig(componentType TiUPComponentType, clusterName,
	configYaml string, args []string, timeout int) (result string, err error) {
	configYamlFilePath, err := disk.CreateWithContent("",
		"tidb-edit-config-topology", "yaml", []byte(configYaml))
	if err != nil {
		return "", err
	}

	tiUPArgs := fmt.Sprintf("%s %s %s %s %s %s %s %d %s", componentType, CMDEditConfig, clusterName,
		CMDTopologyFile, configYamlFilePath, strings.Join(args, " "), FlagWaitTimeout, timeout, CMDYes)
	return m.startSyncOperation(tiUPArgs, timeout, false)
}

func (m *Manager) Reload(componentType TiUPComponentType, clusterName string,
	args []string, timeout int) (result string, err error) {
	tiUPArgs := fmt.Sprintf("%s %s %s %s %s %d %s", componentType, CMDReload,
		clusterName, strings.Join(args, " "), FlagWaitTimeout, timeout, CMDYes)
	return m.startSyncOperation(tiUPArgs, timeout, false)
}
