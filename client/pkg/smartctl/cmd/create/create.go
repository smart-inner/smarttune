package create

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/smart-inner/smarttune/pkg/genericclioptions"
	"github.com/smart-inner/smarttune/util"
	"github.com/smart-inner/smarttune/util/http"
	"github.com/spf13/cobra"
	"html/template"
	"io/ioutil"
	"os"
	"strings"
)

type CreateOptions struct {
	Backend     string
	System      string
	Target      string
	SessionName string

	genericclioptions.IOStreams
}

func NewCreateOptions(streams genericclioptions.IOStreams) *CreateOptions {
	return &CreateOptions{
		IOStreams: streams,
	}
}

func NewCmdCreate(streams genericclioptions.IOStreams) *cobra.Command {
	o := NewCreateOptions(streams)
	cmd := &cobra.Command{
		Use:   "create SESSION_NAME --backend=backend [--system=system] [--target=target]",
		Short: "Create session for the specified system",
		Long: `Create session, which include system type, system version, knobs catalog, metrics catalog
tuning algorithm and target objective.`,
		Run: func(cmd *cobra.Command, args []string) {
			util.CheckErr(o.Create(args))
		},
	}
	addCreateFlags(cmd, o)

	return cmd
}

func addCreateFlags(cmd *cobra.Command, opt *CreateOptions) {
	cmd.Flags().StringVar(&opt.Backend, "backend", "", "The backend url for smarttune, such as '127.0.0.1:5000'")
	cmd.Flags().StringVar(&opt.System, "system", "tidb@v6.1.0", "The system catalog for tuning")
	cmd.Flags().StringVar(&opt.Target, "target", "tidb.tidb_qps", "The target objective for tuning")
}

func (o *CreateOptions) RegisterSystemCatalog(file string) error {
	url := fmt.Sprintf("http://%s/api/system/register", o.Backend)
	content, err := os.ReadFile(file)
	request := make(map[string]interface{})
	if err = json.Unmarshal(content, &request); err != nil {
		return err
	}
	headers := make(map[string]string)
	resp, err := http.PostJSON(url, request, headers)
	if err != nil {
		return err
	}
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	var build strings.Builder
	build.WriteString(string(body))
	build.WriteString("\n")
	if resp.StatusCode != 200 {
		fmt.Fprintf(o.ErrOut, build.String())
	}
	fmt.Fprintf(o.Out, build.String())
	return nil
}

func (o *CreateOptions) RegisterKnobsCatalog(file string) error {
	url := fmt.Sprintf("http://%s/api/knob/register/catalog", o.Backend)
	content, err := os.ReadFile(file)
	request := make(map[string]interface{})
	if err = json.Unmarshal(content, &request); err != nil {
		return err
	}
	headers := make(map[string]string)
	resp, err := http.PostJSON(url, request, headers)
	if err != nil {
		return err
	}
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	var build strings.Builder
	build.WriteString(string(body))
	build.WriteString("\n")
	if resp.StatusCode != 200 {
		fmt.Fprintf(o.ErrOut, build.String())
	}
	fmt.Fprintf(o.Out, build.String())
	return nil
}

func (o *CreateOptions) RegisterMetricsCatalog(file string) error {
	url := fmt.Sprintf("http://%s/api/metric/register/catalog", o.Backend)
	content, err := os.ReadFile(file)
	request := make(map[string]interface{})
	if err = json.Unmarshal(content, &request); err != nil {
		return err
	}
	headers := make(map[string]string)
	resp, err := http.PostJSON(url, request, headers)
	if err != nil {
		return err
	}
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	var build strings.Builder
	build.WriteString(string(body))
	build.WriteString("\n")
	if resp.StatusCode != 200 {
		fmt.Fprintf(o.ErrOut, build.String())
	}
	fmt.Fprintf(o.Out, build.String())
	return nil
}

func (o *CreateOptions) RegisterSession(file string) error {
	t, err := template.ParseFiles(file)
	if err != nil {
		return err
	}

	session := new(bytes.Buffer)
	if err = t.Execute(session, o); err != nil {
		return err
	}
	url := fmt.Sprintf("http://%s/api/session/create", o.Backend)
	request := make(map[string]interface{})
	if err = json.Unmarshal([]byte(session.String()), &request); err != nil {
		return err
	}
	headers := make(map[string]string)
	resp, err := http.PostJSON(url, request, headers)
	if err != nil {
		return err
	}
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	var build strings.Builder
	build.WriteString(string(body))
	build.WriteString("\n")
	if resp.StatusCode != 200 {
		fmt.Fprintf(o.ErrOut, build.String())
	}
	fmt.Fprintf(o.Out, build.String())
	return nil
}

func (o *CreateOptions) RegisterTuningKnobs(file string) error {
	t, err := template.ParseFiles(file)
	if err != nil {
		return err
	}

	tuningKnobs := new(bytes.Buffer)
	if err = t.Execute(tuningKnobs, o); err != nil {
		return err
	}
	url := fmt.Sprintf("http://%s/api/knob/tuning", o.Backend)
	request := make(map[string]interface{})
	if err = json.Unmarshal([]byte(tuningKnobs.String()), &request); err != nil {
		return err
	}
	headers := make(map[string]string)
	resp, err := http.PostJSON(url, request, headers)
	if err != nil {
		return err
	}
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return err
	}
	var build strings.Builder
	build.WriteString(string(body))
	build.WriteString("\n")
	if resp.StatusCode != 200 {
		fmt.Fprintf(o.ErrOut, build.String())
	}
	fmt.Fprintf(o.Out, build.String())
	return nil
}

func (o *CreateOptions) Create(args []string) error {
	if len(args) != 1 || len(o.Backend) == 0 {
		return errors.New(fmt.Sprintf("Error: invalid subcommand "+
			"'smartctl create %s --backend=%s'", strings.Join(args, " "), o.Backend))
	}
	o.SessionName = args[0]
	knobsCatalogFile := fmt.Sprintf("resource/templates/%s/knobs_catalog.json", o.System)
	metricsCatalogFile := fmt.Sprintf("resource/templates/%s/metrics_catalog.json", o.System)
	sessionFile := fmt.Sprintf("resource/templates/%s/session.json", o.System)
	systemCatalogFile := fmt.Sprintf("resource/templates/%s/system_catalog.json", o.System)
	tuningKnobsFile := fmt.Sprintf("resource/templates/%s/tuning_knobs.json", o.System)

	if err := o.RegisterSystemCatalog(systemCatalogFile); err != nil {
		return err
	}

	if err := o.RegisterKnobsCatalog(knobsCatalogFile); err != nil {
		return err
	}

	if err := o.RegisterMetricsCatalog(metricsCatalogFile); err != nil {
		return err
	}

	if err := o.RegisterSession(sessionFile); err != nil {
		return err
	}

	if err := o.RegisterTuningKnobs(tuningKnobsFile); err != nil {
		return err
	}

	return nil
}
